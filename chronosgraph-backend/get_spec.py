import json

with open(r'C:\Users\Niranjana\.gemini\antigravity\brain\3c07f247-289d-4f9c-9395-1f005c4eac2c\.system_generated\logs\transcript.jsonl', encoding='utf-8') as f:
    for line in f:
        if '"type":"USER_INPUT"' in line:
            data = json.loads(line)
            with open('spec.txt', 'w', encoding='utf-8') as out_f:
                out_f.write(data['content'])
            break
