"""
Pricing and cost tracking for AI receptionist calls.

Costs are based on:
- Transcription (Whisper): $0.02 per minute
- Text-to-speech (ElevenLabs): $0.30 per 1M characters
- Text generation (GPT): $0.00015 per 1K input tokens, $0.0006 per 1K output tokens
- Greeting generation (GPT + TTS): bundled pricing
- gTTS fallback: free (but lower quality)

All costs are passed through to the customer with a small margin (configurable).
"""
import os
from decimal import Decimal
from typing import Dict, Tuple

# Pricing per unit (in USD)
PRICING = {
    'whisper_per_minute': Decimal('0.02'),
    'elevenlabs_per_million_chars': Decimal('0.30'),
    'gpt_4o_mini_per_1k_input_tokens': Decimal('0.00015'),
    'gpt_4o_mini_per_1k_output_tokens': Decimal('0.0006'),
    'gpt_4_per_1k_input_tokens': Decimal('0.03'),
    'gpt_4_per_1k_output_tokens': Decimal('0.06'),
}

# Markup (multiply cost by this factor to add margin)
MARGIN_MULTIPLIER = Decimal(os.environ.get('PRICING_MARGIN', '1.3'))  # 30% margin by default

# Minimum charge per call
MINIMUM_CHARGE = Decimal(os.environ.get('MINIMUM_CHARGE_PER_CALL', '0.15'))

# Available TTS providers and models
TTS_PROVIDERS = {
    'elevenlabs': {
        'name': 'ElevenLabs',
        'cost_per_million_chars': PRICING['elevenlabs_per_million_chars'],
        'quality': 'Premium',
        'latency': 'Low',
    },
    'gtts': {
        'name': 'Google TTS (Free)',
        'cost_per_million_chars': Decimal('0'),
        'quality': 'Standard',
        'latency': 'Medium',
    },
}

LLM_MODELS = {
    'gpt-4o-mini': {
        'name': 'GPT-4o Mini (Fast & Cheap)',
        'input_cost_per_1k': PRICING['gpt_4o_mini_per_1k_input_tokens'],
        'output_cost_per_1k': PRICING['gpt_4o_mini_per_1k_output_tokens'],
        'speed': 'Fast',
        'quality': 'Good',
    },
    'gpt-4': {
        'name': 'GPT-4 (Most Powerful)',
        'input_cost_per_1k': PRICING['gpt_4_per_1k_input_tokens'],
        'output_cost_per_1k': PRICING['gpt_4_per_1k_output_tokens'],
        'speed': 'Slow',
        'quality': 'Excellent',
    },
}


def calculate_transcription_cost(duration_seconds: int, provider: str = 'whisper') -> Decimal:
    """Calculate cost for transcription.

    Args:
        duration_seconds: Length of audio to transcribe
        provider: 'whisper' (only option for now)

    Returns:
        Cost in USD (before markup)
    """
    minutes = Decimal(duration_seconds) / Decimal(60)
    cost = minutes * PRICING['whisper_per_minute']
    return cost


def calculate_tts_cost(text: str, provider: str = 'gtts') -> Decimal:
    """Calculate cost for text-to-speech.

    Args:
        text: Text to synthesize
        provider: 'elevenlabs' or 'gtts'

    Returns:
        Cost in USD (before markup)
    """
    if provider == 'gtts':
        return Decimal('0')
    elif provider == 'elevenlabs':
        char_count = Decimal(len(text))
        cost = (char_count / Decimal('1000000')) * PRICING['elevenlabs_per_million_chars']
        return cost
    else:
        return Decimal('0')


def calculate_llm_cost(model: str, input_tokens: int, output_tokens: int) -> Decimal:
    """Calculate cost for LLM completion.

    Args:
        model: 'gpt-4o-mini' or 'gpt-4'
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD (before markup)
    """
    if model not in LLM_MODELS:
        model = 'gpt-4o-mini'

    info = LLM_MODELS[model]
    input_cost = (Decimal(input_tokens) / Decimal(1000)) * info['input_cost_per_1k']
    output_cost = (Decimal(output_tokens) / Decimal(1000)) * info['output_cost_per_1k']
    return input_cost + output_cost


def apply_markup(cost: Decimal) -> Decimal:
    """Apply margin markup to a cost.

    Args:
        cost: Cost in USD

    Returns:
        Cost with markup applied
    """
    return cost * MARGIN_MULTIPLIER


def estimate_call_cost(
    llm_model: str = 'gpt-4o-mini',
    tts_provider: str = 'gtts',
    estimated_duration_seconds: int = 30,
) -> Dict:
    """Estimate the cost of a single call.

    This is a rough estimate based on typical call patterns:
    - ~200 input tokens for greeting
    - ~100 output tokens for greeting
    - ~1 minute of transcription
    - ~200 chars for greeting
    - ~200 input tokens for reply
    - ~50 output tokens for reply
    - ~100 chars for reply

    Minimum charge per call: $0.15

    Args:
        llm_model: 'gpt-4o-mini' or 'gpt-4'
        tts_provider: 'elevenlabs' or 'gtts'
        estimated_duration_seconds: Estimated call length

    Returns:
        Dict with breakdown of costs
    """
    # Transcription cost (typically 30-60 seconds per call)
    trans_cost = calculate_transcription_cost(min(estimated_duration_seconds, 60))

    # TTS costs
    greeting_text = "Hello, thank you for calling. How can I help you today?"
    greeting_tts_cost = calculate_tts_cost(greeting_text, tts_provider)

    reply_text = "I'd be happy to help with that. Let me connect you with the right team."
    reply_tts_cost = calculate_tts_cost(reply_text, tts_provider)

    # LLM costs (estimate)
    # Greeting: ~200 input tokens, ~50 output tokens
    greeting_llm_cost = calculate_llm_cost(llm_model, 200, 50)

    # Reply: ~300 input tokens (including transcription context), ~100 output tokens
    reply_llm_cost = calculate_llm_cost(llm_model, 300, 100)

    subtotal = trans_cost + greeting_tts_cost + greeting_llm_cost + reply_tts_cost + reply_llm_cost
    with_markup = apply_markup(subtotal)
    
    # Apply minimum charge
    final_total = max(with_markup, MINIMUM_CHARGE)

    return {
        'transcription': {
            'cost': float(trans_cost),
            'details': f"{min(estimated_duration_seconds, 60)/60:.1f} min @ {PRICING['whisper_per_minute']}/min",
        },
        'greeting_llm': {
            'cost': float(greeting_llm_cost),
            'details': f"~200 input, ~50 output tokens",
        },
        'greeting_tts': {
            'cost': float(greeting_tts_cost),
            'details': f"{len(greeting_text)} chars @ ${TTS_PROVIDERS[tts_provider]['cost_per_million_chars']}/M",
        },
        'reply_llm': {
            'cost': float(reply_llm_cost),
            'details': f"~300 input, ~100 output tokens",
        },
        'reply_tts': {
            'cost': float(reply_tts_cost),
            'details': f"{len(reply_text)} chars @ ${TTS_PROVIDERS[tts_provider]['cost_per_million_chars']}/M",
        },
        'subtotal': float(subtotal),
        'margin': float(with_markup - subtotal),
        'total': float(final_total),
        'minimum_applied': final_total > with_markup,
    }


def format_price(value: float) -> str:
    """Format a price for display."""
    return f"${value:.4f}"
