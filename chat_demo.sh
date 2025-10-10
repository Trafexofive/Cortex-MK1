#!/bin/bash
# Interactive Chat Demo

echo "🤖 Cortex AI Chat - Interactive Demo"
echo "====================================="
echo ""
echo "Type your messages below. Type 'exit' to quit."
echo ""

while true; do
    echo -n "You: "
    read -r user_input
    
    if [ "$user_input" = "exit" ]; then
        echo "Goodbye! 👋"
        break
    fi
    
    if [ -z "$user_input" ]; then
        continue
    fi
    
    echo -n "AI: "
    curl -s -X POST http://localhost:8081/completion \
        -H "Content-Type: application/json" \
        -d "{\"messages\": [{\"role\": \"user\", \"content\": $(echo "$user_input" | jq -Rs .)}]}" \
        | jq -r '.content'
    
    echo ""
done
