# Example Test Scenarios (Hiring Manager Conversations)

## Scenario 1: End-to-end run
```
manager> run data/job_description.txt
manager> show shortlist
manager> why cand_004
manager> compare cand_004,cand_002,cand_007
```

## Scenario 2: Skill-specific search
```
manager> find react 3+ years
manager> find python langgraph llm
```

## Scenario 3: Mid-conversation requirement update
```
manager> update must=react,typescript,sql nice=aws,azure years=3
manager> show shortlist
manager> why cand_001
```

## Scenario 4: Re-run ranking after feedback
```
manager> rerank
manager> show shortlist
```

## Scenario 5: Interview preparation
```
manager> questions cand_004
manager> questions cand_002
```

## Scenario 6: Decision support
```
manager> compare cand_004,cand_001
manager> why cand_004
manager> why cand_001
```
