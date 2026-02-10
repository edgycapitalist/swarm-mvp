"""
Simulation orchestrator - main execution logic
"""
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.conf import settings

from audiences.models import AgentProfile
from stimuli.models import Stimulus
from .models import SimulationRun, AgentResponse, RunAggregate
from .prompts import build_day1_prompt, build_day7_prompt, build_social_summary
from gemini.client import GeminiClient
from gemini.exceptions import GeminiError

logger = logging.getLogger(__name__)


class SimulationOrchestrator:
    """
    Orchestrates simulation execution across agents and phases.
    """
    
    def __init__(self, run: SimulationRun):
        self.run = run
        self.gemini_client = GeminiClient()
        self.errors: List[str] = []
        
    def execute(self) -> SimulationRun:
        """
        Execute the full simulation run.
        
        Returns:
            Updated SimulationRun with results
        """
        logger.info(f"Starting simulation run {self.run.id}")
        
        # Update status
        self.run.status = 'running'
        self.run.started_at = timezone.now()
        self.run.save()
        
        try:
            # Get agents
            agents = list(self.run.segment.agents.all())
            if not agents:
                raise ValueError("No agents found for this segment. Generate agents first.")
            
            self.run.agent_count = len(agents)
            self.run.save()
            
            # Execute each phase
            phases = self.run.phases or settings.SIM_PHASES_DEFAULT
            
            for phase in phases:
                logger.info(f"Executing phase {phase} for {len(agents)} agents")
                self._execute_phase(phase, agents)
            
            # Final status
            if self.errors:
                self.run.status = 'partial'
                self.run.error_summary = "\n".join(self.errors[-10:])  # Keep last 10 errors
                self.run.error_count = len(self.errors)
            else:
                self.run.status = 'completed'
            
            self.run.completed_at = timezone.now()
            self.run.save()
            
            logger.info(f"Simulation run {self.run.id} completed with status: {self.run.status}")
            
        except Exception as e:
            logger.error(f"Simulation run {self.run.id} failed: {e}")
            self.run.status = 'failed'
            self.run.error_summary = str(e)
            self.run.completed_at = timezone.now()
            self.run.save()
            raise
        
        return self.run
    
    def _execute_phase(self, phase: str, agents: List[AgentProfile]):
        """Execute a single phase for all agents"""
        
        # Get stimulus data
        stimulus_data = {
            'channel': self.run.stimulus.channel,
            'scenario': self.run.stimulus.scenario_tag,
            'sender': self.run.stimulus.sender_name,
            'context': self.run.stimulus.context_text,
            'message': self.run.stimulus.message_text,
        }
        
        # Get Day 1 responses if this is Day 7+
        day1_responses = []
        social_summary = ""
        if phase in ['D7', 'D30', 'D90']:
            day1_responses = list(
                AgentResponse.objects.filter(run=self.run, phase='D1')
                .values('agent_id', 'approval_score', 'intent_label', 'verbatim_text', 'emotions_json')
            )
            social_summary = build_social_summary([
                {
                    'approval': r['approval_score'],
                    'intent': r['intent_label'],
                    'verbatim': r['verbatim_text']
                }
                for r in day1_responses
            ])
        
        responses_data = []
        
        for agent in agents:
            try:
                response_data = self._process_agent(
                    agent, phase, stimulus_data, 
                    day1_responses, social_summary
                )
                responses_data.append(response_data)
            except Exception as e:
                error_msg = f"Agent {agent.display_name} phase {phase}: {e}"
                logger.warning(error_msg)
                self.errors.append(error_msg)
        
        # Compute and save aggregates
        if responses_data:
            self._compute_aggregates(phase, responses_data)
    
    def _process_agent(
        self,
        agent: AgentProfile,
        phase: str,
        stimulus_data: dict,
        day1_responses: list,
        social_summary: str
    ) -> dict:
        """Process a single agent for a phase"""
        
        start_time = time.time()
        
        # Get segment style guide
        segment_style = agent.segment.style_guide_json or {}
        
        # Build prompt based on phase
        if phase == 'D1':
            prompt = build_day1_prompt(
                agent_traits=agent.traits_json,
                stimulus=stimulus_data,
                segment_style=segment_style
            )
        else:
            # Get this agent's Day 1 response
            agent_day1 = None
            for r in day1_responses:
                if str(r['agent_id']) == str(agent.id):
                    agent_day1 = {
                        'approval': r['approval_score'],
                        'intent': r['intent_label'],
                        'verbatim': r['verbatim_text']
                    }
                    break
            
            if not agent_day1:
                agent_day1 = {'approval': 5, 'intent': 'ignore', 'verbatim': 'No initial response'}
            
            prompt = build_day7_prompt(
                agent_traits=agent.traits_json,
                stimulus=stimulus_data,
                segment_style=segment_style,
                day1_response=agent_day1,
                social_summary=social_summary
            )
        
        # Call Gemini
        response_data = self.gemini_client.generate_agent_response(prompt)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Save response
        agent_response = AgentResponse.objects.create(
            run=self.run,
            agent=agent,
            phase=phase,
            approval_score=response_data['approval'],
            emotions_json=response_data['emotions'],
            intent_label=response_data['intent'],
            intent_confidence=response_data['intent_confidence'],
            verbatim_text=response_data['verbatim'],
            raw_json=response_data if settings.STORE_RAW_LLM_OUTPUT else None,
            processing_time_ms=processing_time
        )
        
        # Update agent memory
        memory_update = f"[{phase}] Saw message about {stimulus_data.get('scenario', 'topic')}. " \
                       f"Reaction: {response_data['intent']} (approval: {response_data['approval']}/10)"
        agent.memory_text = (agent.memory_text + "\n" + memory_update).strip()
        agent.save()
        
        return response_data
    
    def _compute_aggregates(self, phase: str, responses: List[dict]):
        """Compute and save aggregate statistics for a phase"""
        
        if not responses:
            return
        
        # Approval stats
        approvals = [r['approval'] for r in responses]
        avg_approval = sum(approvals) / len(approvals)
        
        # Approval distribution
        distribution = {str(i): 0 for i in range(1, 11)}
        for a in approvals:
            distribution[str(a)] = distribution.get(str(a), 0) + 1
        
        # Emotion means
        emotion_sums = {}
        for r in responses:
            for emotion, value in r.get('emotions', {}).items():
                emotion_sums[emotion] = emotion_sums.get(emotion, 0) + value
        emotion_means = {e: v / len(responses) for e, v in emotion_sums.items()}
        
        # Intent counts
        intent_counts = {}
        for r in responses:
            intent = r.get('intent', 'ignore')
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Sample verbatims (top positive, top negative, random)
        sorted_by_approval = sorted(responses, key=lambda x: x['approval'], reverse=True)
        representative_quotes = [
            {'type': 'most_positive', 'approval': sorted_by_approval[0]['approval'], 
             'text': sorted_by_approval[0]['verbatim']},
            {'type': 'most_negative', 'approval': sorted_by_approval[-1]['approval'],
             'text': sorted_by_approval[-1]['verbatim']},
        ]
        
        # Save aggregate
        RunAggregate.objects.update_or_create(
            run=self.run,
            phase=phase,
            defaults={
                'response_count': len(responses),
                'avg_approval': round(avg_approval, 2),
                'approval_distribution': distribution,
                'emotion_means_json': {k: round(v, 3) for k, v in emotion_means.items()},
                'intent_counts_json': intent_counts,
                'representative_quotes': representative_quotes,
            }
        )


def run_simulation(run: SimulationRun) -> SimulationRun:
    """
    Entry point for running a simulation.
    
    Args:
        run: The SimulationRun to execute
        
    Returns:
        Updated SimulationRun with results
    """
    orchestrator = SimulationOrchestrator(run)
    return orchestrator.execute()