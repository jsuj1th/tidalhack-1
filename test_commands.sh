#!/bin/bash
# Test commands for hackathon feedback agent

echo "🚀 Testing Hackathon Feedback Agent"
echo "=================================="

# Test 1: Health check
echo -e "\n1. Health check..."
curl -X GET http://127.0.0.1:8001/health 2>/dev/null || echo "Health endpoint not available"

# Test 2: Send initial message
echo -e "\n2. Sending initial greeting..."
curl -X POST http://127.0.0.1:8001/submit \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "msg_id": "'$(uuidgen)'",
    "content": [
      {"type": "text", "text": "Hi, I want to give feedback about the hackathon"}
    ]
  }' 2>/dev/null

echo -e "\n\nWaiting 3 seconds..."
sleep 3

# Test 3: Send feedback
echo -e "\n3. Sending feedback..."
curl -X POST http://127.0.0.1:8001/submit \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "msg_id": "'$(uuidgen)'",
    "content": [
      {"type": "text", "text": "I am excited about learning AI and machine learning at this hackathon. I hope there will be good workshops on neural networks and opportunities to network with other developers. I would also like to see some mentorship from industry experts."}
    ]
  }' 2>/dev/null

echo -e "\n\n✅ Test commands completed!"
echo "Check your agent terminal for responses and logs."