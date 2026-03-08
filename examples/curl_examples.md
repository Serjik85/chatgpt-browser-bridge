POST /chat

curl -X POST http://127.0.0.1:8080/chat
-H "Content-Type: application/json"
-d '{"message":"Hello"}'

POST /v1/chat/completions
curl http://127.0.0.1:8080/v1/chat/completions

-H "Content-Type: application/json"
-d '{
"model":"chatgpt",
"messages":[
{"role":"user","content":"Hello"}
]
}'
