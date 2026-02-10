"""
Prompt templates for simulation phases
"""
from gemini.schemas import get_schema_instructions


def build_day1_prompt(agent_traits: dict, stimulus: dict, segment_style: dict) -> str:
    """
    Build the prompt for Day 1 (initial reaction).
    
    Args:
        agent_traits: The agent's specific traits
        stimulus: The stimulus being tested
        segment_style: Communication style guide from segment
    """
    
    schema_instructions = get_schema_instructions()
    
    prompt = f"""You are simulating the response of a specific person to a message/announcement.

## PERSON PROFILE
- Age: {agent_traits.get('age', 30)}
- Gender: {agent_traits.get('gender', 'not specified')}
- Location: {agent_traits.get('location', 'MENA region')}
- Education: {agent_traits.get('education', 'bachelor')}
- Income level: {agent_traits.get('income_level', 'middle')}

Personality traits (0-1 scale):
- Openness to new ideas: {agent_traits.get('openness', 0.5)}
- Skepticism toward marketing: {agent_traits.get('skepticism', 0.5)}
- Traditionalism: {agent_traits.get('traditionalism', 0.5)}
- Tech savviness: {agent_traits.get('tech_savviness', 0.5)}

Attitudes toward relevant topics:
{_format_attitudes(agent_traits.get('attitudes', {}))}

Communication style:
- Formality: {segment_style.get('formality', 'moderate')}
- Emoji usage: {segment_style.get('emoji_usage', 'occasional')}
- Dialect preference: {segment_style.get('dialect', 'Modern Standard Arabic/English mix')}

## THE MESSAGE THEY ARE SEEING
Channel: {stimulus.get('channel', 'social media')}
Scenario: {stimulus.get('scenario', 'general announcement')}
Sender: {stimulus.get('sender', 'Unknown organization')}

Context: {stimulus.get('context', '')}

Message:
\"\"\"{stimulus.get('message', '')}\"\"\"

## YOUR TASK
Respond AS this person, showing their genuine Day 1 reaction (first impression) to this message.
Consider:
- Their demographics and values
- Their personality traits
- Their likely prior experience with similar messages
- Cultural context of their region

{schema_instructions}
"""
    return prompt


def build_day7_prompt(
    agent_traits: dict,
    stimulus: dict,
    segment_style: dict,
    day1_response: dict,
    social_summary: str
) -> str:
    """
    Build the prompt for Day 7 (after social processing).
    
    Args:
        agent_traits: The agent's specific traits
        stimulus: The stimulus being tested
        segment_style: Communication style guide
        day1_response: This agent's Day 1 response
        social_summary: Summary of overall Day 1 reactions
    """
    
    schema_instructions = get_schema_instructions()
    
    prompt = f"""You are simulating how a specific person's opinion has evolved ONE WEEK after seeing a message.

## PERSON PROFILE
- Age: {agent_traits.get('age', 30)}
- Gender: {agent_traits.get('gender', 'not specified')}
- Location: {agent_traits.get('location', 'MENA region')}
- Personality: Openness {agent_traits.get('openness', 0.5)}, Skepticism {agent_traits.get('skepticism', 0.5)}

## THE ORIGINAL MESSAGE (from 7 days ago)
Channel: {stimulus.get('channel', 'social media')}
Message summary: {stimulus.get('message', '')[:200]}...

## THEIR INITIAL REACTION (Day 1)
Approval: {day1_response.get('approval', 5)}/10
Initial feeling: {day1_response.get('verbatim', 'No comment')}
Initial intent: {day1_response.get('intent', 'ignore')}

## WHAT HAPPENED DURING THE WEEK
Social media discussion and reactions from others:
{social_summary}

## YOUR TASK
Show how this person's opinion has evolved after:
- Seeing others' reactions
- Having time to think about it
- Possibly discussing with friends/family
- Seeing any follow-up news or responses

Their opinion may have:
- Strengthened (if they saw support for their view)
- Softened (if they saw good counter-arguments)
- Stayed the same (if nothing changed their mind)
- Reversed (if new information was compelling)

{schema_instructions}
"""
    return prompt


def build_social_summary(day1_responses: list) -> str:
    """
    Build a summary of Day 1 responses to use in Day 7 prompts.
    This simulates what the agent would see on social media.
    """
    if not day1_responses:
        return "Limited public discussion was observed."
    
    # Calculate stats
    approvals = [r.get('approval', 5) for r in day1_responses]
    avg_approval = sum(approvals) / len(approvals)
    
    # Count intents
    intents = {}
    for r in day1_responses:
        intent = r.get('intent', 'ignore')
        intents[intent] = intents.get(intent, 0) + 1
    
    # Get sample verbatims
    positive_samples = [r.get('verbatim', '') for r in day1_responses if r.get('approval', 5) >= 7][:2]
    negative_samples = [r.get('verbatim', '') for r in day1_responses if r.get('approval', 5) <= 4][:2]
    
    summary = f"""Overall public reaction: {'Positive' if avg_approval >= 6 else 'Mixed' if avg_approval >= 4 else 'Negative'} (average approval: {avg_approval:.1f}/10)

Common reactions observed:
- {intents.get('share_positive', 0)} people shared positively
- {intents.get('share_negative', 0)} people shared with criticism  
- {intents.get('engage_supportive', 0)} left supportive comments
- {intents.get('engage_critical', 0)} left critical comments
- {intents.get('oppose_actively', 0)} actively opposed it

Sample supportive comments seen online:
{chr(10).join(['- "' + s[:100] + '..."' for s in positive_samples]) if positive_samples else '- (few supportive comments)'}

Sample critical comments seen online:
{chr(10).join(['- "' + s[:100] + '..."' for s in negative_samples]) if negative_samples else '- (few critical comments)'}
"""
    return summary


def _format_attitudes(attitudes: dict) -> str:
    """Format attitudes dictionary for prompt"""
    if not attitudes:
        return "- No specific attitudes recorded"
    
    lines = []
    for topic, score in attitudes.items():
        if isinstance(score, (int, float)):
            sentiment = "positive" if score > 0.6 else "neutral" if score > 0.4 else "negative"
            lines.append(f"- {topic}: {sentiment} ({score:.1f})")
        else:
            lines.append(f"- {topic}: {score}")
    
    return "\n".join(lines) if lines else "- No specific attitudes recorded"