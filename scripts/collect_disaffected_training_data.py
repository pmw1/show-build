#!/usr/bin/env python3
"""
Collect training data for Disaffected-style social media content
Uses Grok API to generate sassy, on-brand tweets and commentary
"""

import json
import requests
import os
from datetime import datetime

GROK_API_KEY = os.getenv("XAI_API_KEY", "")
GROK_API_URL = "https://api.x.ai/v1/chat/completions"

if not GROK_API_KEY:
    raise ValueError("XAI_API_KEY environment variable not set. Add it to .env file.")

system_prompt = """You are a social media manager for Disaffected, a provocative political and cultural commentary show.

Your voice is:
- Edgy but substantive
- Sarcastic but insightful
- Provocative but not trolling
- Critical of establishment narratives
- Skeptical of mainstream media
- Raw and unfiltered
- Focused on political/cultural hypocrisy

Write tweets and commentary that are clever, biting, and on-brand for a show that challenges conventional wisdom."""

# Topics aligned with Disaffected content
prompts = [
    # Political commentary
    "Write a tweet about mainstream media bias in political coverage",
    "Comment on political theater vs actual policy",
    "Tweet about establishment politicians pretending to be outsiders",
    "Write about the performative nature of modern politics",
    "Comment on media narratives vs reality",

    # Cultural commentary
    "Write a tweet about Karen culture and performative outrage",
    "Comment on cancel culture hypocrisy",
    "Tweet about virtue signaling in corporations",
    "Write about the attention economy and social media",
    "Comment on identity politics vs class issues",

    # Media criticism
    "Write a tweet criticizing 24/7 news cycle sensationalism",
    "Comment on how cable news manufactures outrage",
    "Tweet about independent media vs corporate media",
    "Write about fact-checking that ignores context",
    "Comment on journalists being activists",

    # Event commentary (current topics)
    "Write a tweet about Trump rally security failures",
    "Comment on Biden's age and media coverage",
    "Tweet about classified documents scandals",
    "Write about immigration policy theater",
    "Comment on Ukraine funding debates",

    # Social observations
    "Write a tweet about how social media rewards extremism",
    "Comment on the death of nuance in public discourse",
    "Tweet about how everyone thinks they're the resistance",
    "Write about tribalism in modern politics",
    "Comment on conspiracy theories going mainstream",

    # Show-specific content
    "Write a tweet promoting a segment about political hypocrisy",
    "Comment on why mainstream narratives fail",
    "Tweet about exposing media manipulation",
    "Write about giving voice to unpopular truths",
    "Comment on why Disaffected covers stories others won't",

    # Reactions to absurdity
    "Write a sarcastic tweet about politicians pretending to care",
    "Comment on the absurdity of modern political discourse",
    "Tweet about media double standards",
    "Write about how everyone claims to be silenced while having massive platforms",
    "Comment on the gap between elite rhetoric and working-class reality",

    # Provocative takes
    "Write a tweet challenging popular narratives about current events",
    "Comment on why the 'good guys vs bad guys' framing is bullshit",
    "Tweet about inconvenient truths both sides ignore",
    "Write about manufactured controversies distracting from real issues",
    "Comment on how outrage is a business model",
]

def get_grok_response(prompt):
    """Get sassy, on-brand response from Grok"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "model": "grok-4-latest",
        "stream": False,
        "temperature": 1.1  # Slightly higher for creativity
    }

    try:
        response = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def collect_training_data(num_rounds=1):
    """Collect training examples from Grok"""
    training_data = []
    total_prompts = len(prompts) * num_rounds

    print(f"Collecting {total_prompts} training examples...")
    print(f"Estimated cost: ${total_prompts * 0.02:.2f}")
    print()

    for round_num in range(num_rounds):
        print(f"Round {round_num + 1}/{num_rounds}")

        for i, prompt in enumerate(prompts):
            print(f"  [{i+1}/{len(prompts)}] {prompt[:60]}...", end=" ")

            response = get_grok_response(prompt)

            if response:
                example = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response}
                    ]
                }
                training_data.append(example)
                print(f"✓ ({len(response)} chars)")
            else:
                print(f"✗ Failed")

    # Save to JSONL
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'disaffected_training_data_{timestamp}.jsonl'

    with open(filename, 'w') as f:
        for example in training_data:
            f.write(json.dumps(example) + '\n')

    print()
    print(f"✓ Saved {len(training_data)} examples to {filename}")
    print(f"Actual cost estimate: ~${len(training_data) * 0.02:.2f}")

    # Show a sample
    if training_data:
        print("\nSample response:")
        print("-" * 80)
        sample = training_data[0]
        print(f"Prompt: {sample['messages'][1]['content']}")
        print(f"Response: {sample['messages'][2]['content']}")
        print("-" * 80)

    return filename

if __name__ == "__main__":
    import sys

    # Allow specifying number of rounds
    num_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    print("=" * 80)
    print("Disaffected Training Data Collection")
    print("=" * 80)
    print()

    filename = collect_training_data(num_rounds)

    print()
    print("Next steps:")
    print(f"1. Review {filename} for quality")
    print(f"2. Run multiple times with different rounds to get 100-200 examples")
    print(f"3. Use this data to fine-tune your local model")
    print(f"4. Deploy to Ollama for free social media content generation")
