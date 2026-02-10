"""
Agent generation logic - creates individual agents from segment templates
"""
import random
from typing import List
from .models import AudienceSegment, AgentProfile


# Arabic/MENA first names for realistic agent names
ARABIC_MALE_NAMES = [
    "Mohammed", "Ahmed", "Ali", "Omar", "Khalid", "Youssef", "Hassan", "Ibrahim",
    "Faisal", "Abdullah", "Saeed", "Tariq", "Nasser", "Hamad", "Salem", "Rashid",
    "Majid", "Fahad", "Sultan", "Waleed"
]

ARABIC_FEMALE_NAMES = [
    "Fatima", "Aisha", "Mariam", "Noura", "Sara", "Layla", "Hana", "Reem",
    "Dana", "Lina", "Noor", "Yasmin", "Salma", "Huda", "Amira", "Dalia",
    "Maha", "Lubna", "Rana", "Asma"
]


def generate_agent_name(gender: str = None) -> str:
    """Generate a realistic Arabic name"""
    if gender == 'female':
        return random.choice(ARABIC_FEMALE_NAMES)
    elif gender == 'male':
        return random.choice(ARABIC_MALE_NAMES)
    else:
        # Random gender
        return random.choice(ARABIC_MALE_NAMES + ARABIC_FEMALE_NAMES)


def generate_agent_traits(segment: AudienceSegment, seed: int = None) -> dict:
    """
    Generate specific agent traits from segment template.
    Adds controlled randomness for diversity.
    """
    if seed:
        random.seed(seed)
    
    demographics = segment.demographics_json or {}
    attitudes = segment.attitudes_json or {}
    style = segment.style_guide_json or {}
    
    # Parse age range and pick specific age
    age_range = demographics.get('age_range', '25-40')
    if '-' in str(age_range):
        min_age, max_age = map(int, str(age_range).split('-'))
    else:
        min_age, max_age = 25, 40
    
    # Generate specific traits with variation
    traits = {
        'age': random.randint(min_age, max_age),
        'gender': random.choice(demographics.get('gender_options', ['male', 'female'])),
        'location': random.choice(demographics.get('locations', ['Riyadh', 'Dubai', 'Cairo'])),
        'education': random.choice(demographics.get('education_levels', ['bachelor', 'master'])),
        'income_level': random.choice(demographics.get('income_levels', ['middle', 'upper-middle'])),
        
        # Personality traits (0-1 scale)
        'openness': round(random.uniform(0.3, 0.9), 2),
        'skepticism': round(random.uniform(0.2, 0.8), 2),
        'traditionalism': round(random.uniform(0.3, 0.8), 2),
        'tech_savviness': round(random.uniform(0.4, 0.95), 2),
        
        # Copy attitudes with slight variation
        'attitudes': {
            k: round(v + random.uniform(-0.15, 0.15), 2) if isinstance(v, (int, float)) else v
            for k, v in attitudes.items()
        },
        
        # Communication style
        'formality': style.get('formality', 'moderate'),
        'emoji_usage': style.get('emoji_usage', 'occasional'),
        'dialect': style.get('dialect', 'MSA'),  # Modern Standard Arabic
    }
    
    return traits


def generate_agents_for_segment(
    segment: AudienceSegment,
    count: int = 20,
    seed: int = None
) -> List[AgentProfile]:
    """
    Generate multiple agent profiles from a segment template.
    
    Args:
        segment: The segment template to generate from
        count: Number of agents to create
        seed: Random seed for reproducibility
    
    Returns:
        List of created AgentProfile objects
    """
    if seed:
        random.seed(seed)
    
    agents = []
    
    for i in range(count):
        # Generate traits with unique seed per agent
        agent_seed = (seed + i) if seed else None
        traits = generate_agent_traits(segment, seed=agent_seed)
        
        # Generate name matching gender
        name = generate_agent_name(gender=traits.get('gender'))
        
        # Make name unique by adding number if needed
        display_name = f"{name}_{i+1}"
        
        agent = AgentProfile.objects.create(
            segment=segment,
            display_name=display_name,
            traits_json=traits,
            memory_text=""
        )
        agents.append(agent)
    
    return agents