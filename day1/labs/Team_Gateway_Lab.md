# Team Gateway Lab: build your own AI gateway

**Machine you will use:** `team-vm-a` (blank Ubuntu server)
**Time:** about 90 minutes
**You work in pairs.** One person types (Builder), the other reads each step aloud and checks it (Navigator). Swap roles after every Part.

## What you are building

Today your whole team uses AI models through one **central gateway**. You will build your **own small gateway** on `team-vm-a`. It sits in front of the central one and adds three controls:

- **A key for each person.** You can revoke one key without touching the others.
- **A request limit and a spending budget** on every key.
- **A fallback.** If one model fails, the gateway uses another.

```
Your VM  ->  YOUR gateway (team-vm-a)  ->  Central gateway  ->  AI models
```

You do not need to know coding. Every step is **copy, paste, press Enter, check the result**.

## How to read this guide

- A grey box is a command. Copy it, paste it, press Enter.
- **Expect:** is what you should see. If you see something else, go to the **Problems** table at the end.
- Wait for each command to finish before you paste the next one.
- Never paste keys in chat or email.

## Your values (get these from the trainer, write them here)

| What | Value |
|---|---|
| team-vm-a address | `172.16.0.38` |
| team-vm-a user | `azureuser` |
| team-vm-a password | (from your team card) |
| Central gateway address | `172.16.0.6` |
| Team key | (from your team card) |

---

## Part 0. Log in to team-vm-a

On **your own lab VM**, open PowerShell and run:

```
ssh azureuser@172.16.0.38
```

Type `yes` the first time, then the password. Typing the password shows nothing on screen. That is normal.

**Expect:** a prompt that starts with `azureuser@team-vm-a`.
From now on, every command in Parts 1 to 5 runs on **team-vm-a**.

---

## Part 1. Check you can reach the central gateway (5 min)

First tell the server your values. Replace the two `PASTE_...` words and keep everything else. Then paste the block.

```
export CENTRAL_IP=172.16.0.6
export TEAM_KEY=PASTE_YOUR_TEAM_KEY_HERE
```

Check the central gateway is alive:

```
curl -s http://$CENTRAL_IP:4000/health/liveliness
```

**Expect:** a short message like `"I'm alive!"`.

Now list the models your team key can use:

```
curl -s http://$CENTRAL_IP:4000/v1/models -H "Authorization: Bearer $TEAM_KEY" | python3 -m json.tool | grep '"id"'
```

**Expect:** two or more lines like `"id": "model-name"`.
**Write down the first two model names** (the text inside the second pair of quotes). You will use them in Part 3.

> No answer, or "Connection refused"? Check the address. Still stuck? See Problems.

---

## Part 2. Install Docker (10 min)

Docker is the program that runs the gateway in a box. Paste these one at a time.

```
curl -fsSL https://get.docker.com | sudo sh
```

**Expect:** lots of text for 1 to 2 minutes, ending with Docker installed.

```
sudo usermod -aG docker $USER
```

Now log out and log back in so the change works:

```
exit
```

Then log in again from your lab VM:

```
ssh azureuser@172.16.0.38
```

Check Docker works:

```
docker --version
docker compose version
```

**Expect:** two version lines, with no errors.

---

## Part 3. Create the gateway files (15 min)

You will make a folder and three small files. Paste each block exactly as shown.

### 3.1 Your values again

The login restart cleared them, so set them again. Replace the `PASTE_...` words. Use the **two model names** you wrote down in Part 1.

```
export CENTRAL_IP=172.16.0.6
export TEAM_KEY=PASTE_YOUR_TEAM_KEY_HERE
export MODEL1=PASTE_FIRST_MODEL_NAME_HERE
export MODEL2=PASTE_SECOND_MODEL_NAME_HERE
```

### 3.2 Make the folder

```
mkdir -p ~/gateway && cd ~/gateway
```

### 3.3 File 1: secrets file (`.env`)

This creates a random admin password (the "master key") and a database password for you.

```
cat > .env <<EOF
LITELLM_MASTER_KEY=sk-team-$(openssl rand -hex 16)
DB_PASSWORD=$(openssl rand -hex 12)
UPSTREAM_BASE=http://$CENTRAL_IP:4000/v1
UPSTREAM_KEY=$TEAM_KEY
EOF
```

Check it:

```
cat .env
```

**Expect:** four lines, and none of them is empty. The `LITELLM_MASTER_KEY` is your admin key. Treat it like a root password.

### 3.4 File 2: the gateway settings (`config.yaml`)

This file says which models you offer and what to do when one fails.

```
cat > config.yaml <<EOF
model_list:
  - model_name: team-chat
    litellm_params:
      model: openai/$MODEL1
      api_base: os.environ/UPSTREAM_BASE
      api_key: os.environ/UPSTREAM_KEY
      input_cost_per_token: 0.0000006
      output_cost_per_token: 0.0000025

  - model_name: team-chat-b
    litellm_params:
      model: openai/$MODEL2
      api_base: os.environ/UPSTREAM_BASE
      api_key: os.environ/UPSTREAM_KEY
      input_cost_per_token: 0.0000003
      output_cost_per_token: 0.0000012

router_settings:
  num_retries: 2
  timeout: 60
  allowed_fails: 2
  cooldown_time: 30
  fallbacks: [{"team-chat": ["team-chat-b"]}]

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL

litellm_settings:
  drop_params: true
EOF
```

Check it:

```
cat config.yaml
```

**Expect:** your two real model names next to `openai/`. If you still see the words `PASTE` or a blank after `openai/`, repeat 3.1 and then this step.

What the settings mean, in plain words:

| Setting | Meaning |
|---|---|
| `team-chat`, `team-chat-b` | The names your teammates will use |
| `input_cost_per_token` and `output_cost_per_token` | Prices, so the gateway can count money spent |
| `fallbacks` | If `team-chat` fails, use `team-chat-b` |
| `num_retries`, `timeout` | Try again twice, and give up on a call after 60 seconds |

### 3.5 File 3: how to start everything (`docker-compose.yml`)

```
cat > docker-compose.yml <<'EOF'
services:
  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_USER: litellm
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: litellm
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U litellm -d litellm"]
      interval: 5s
      timeout: 5s
      retries: 10

  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    restart: unless-stopped
    ports:
      - "4000:4000"
    env_file: .env
    environment:
      DATABASE_URL: postgresql://litellm:${DB_PASSWORD}@db:5432/litellm
    volumes:
      - ./config.yaml:/app/config.yaml
    command: ["--config", "/app/config.yaml", "--port", "4000"]
    depends_on:
      db:
        condition: service_healthy

volumes:
  pgdata:
EOF
```

Check all three files exist:

```
ls
```

**Expect:** `config.yaml  docker-compose.yml` (`.env` is hidden, which is fine).

---

## Part 4. Start the gateway and test it (15 min)

```
docker compose up -d
```

**Expect:** downloads for 2 to 5 minutes, then `Started` or `Healthy`.

Watch it start. Press `Ctrl+C` to leave when you see a line that says the server is running:

```
docker compose logs -f litellm
```

Now test it. These lines load your admin key, then check the gateway is alive:

```
export GW=http://localhost:4000
export MK=$(grep LITELLM_MASTER_KEY .env | cut -d= -f2)
curl -s $GW/health/liveliness
```

**Expect:** `"I'm alive!"`

Send your first question through **your** gateway:

```
curl -s $GW/v1/chat/completions -H "Authorization: Bearer $MK" -H "Content-Type: application/json" -d '{"model":"team-chat","messages":[{"role":"user","content":"Reply with the word ready"}],"max_tokens":10}'
```

**Expect:** a block of text that contains `ready`. **You now have a working gateway.**

> If you edit `config.yaml` later, apply it with `docker compose restart litellm`. If you edit `.env`, use `docker compose up -d --force-recreate litellm`.

---

## Part 5. Create a key for each person (10 min)

First create a small helper. It makes a key with a limit of 30 requests a minute and a budget of 1 dollar a day.

```
mk_key () { curl -s $GW/key/generate -H "Authorization: Bearer $MK" -H "Content-Type: application/json" -d "{\"key_alias\":\"$1\",\"models\":[\"team-chat\",\"team-chat-b\"],\"rpm_limit\":${2:-30},\"max_budget\":${3:-1},\"budget_duration\":\"1d\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['key'])"; }
```

Now make one key for each of you:

```
mk_key person1
mk_key person2
```

**Expect:** each command prints a key that starts with `sk-`. **Copy each key into a private note.** Give each key only to its owner.

Open the admin page in the browser on your lab VM:

```
http://172.16.0.38:4000/ui
```

Username `admin`. Password is your master key (`cat .env` shows it). Find your two keys and their limits.

---

## Part 6. Use your gateway from your own VM (10 min)

Go back to your own lab VM (type `exit` to leave team-vm-a). Use **PowerShell**. Replace `PASTE_PERSON1_KEY`.

```
$key = "PASTE_PERSON1_KEY"
$h = @{Authorization = "Bearer $key"}
Invoke-RestMethod http://172.16.0.38:4000/v1/models -Headers $h
```

**Expect:** a list that has `team-chat` and `team-chat-b`.

Ask a question:

```
$body = @{model="team-chat"; messages=@(@{role="user"; content="Reply with the word ready"}); max_tokens=10} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri http://172.16.0.38:4000/v1/chat/completions -Headers $h -ContentType "application/json" -Body $body
```

**Expect:** an answer that contains `ready`. Then open the admin page again. You should see that request counted under `person1`.

---

## Part 7. Break it on purpose (25 min)

Go back to team-vm-a (`ssh azureuser@172.16.0.38`, then `cd ~/gateway`). Load your helper again, because a new login clears it:

```
cd ~/gateway
export GW=http://localhost:4000
export MK=$(grep LITELLM_MASTER_KEY .env | cut -d= -f2)
mk_key () { curl -s $GW/key/generate -H "Authorization: Bearer $MK" -H "Content-Type: application/json" -d "{\"key_alias\":\"$1\",\"models\":[\"team-chat\",\"team-chat-b\"],\"rpm_limit\":${2:-30},\"max_budget\":${3:-1},\"budget_duration\":\"1d\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['key'])"; }
```

For every test: **write your guess first**, then run it, then write what you saw.

### Test 1. A leaked key is revoked

```
K=$(mk_key victim)
curl -s $GW/v1/models -H "Authorization: Bearer $K" | head -c 200; echo
curl -s $GW/key/delete -H "Authorization: Bearer $MK" -H "Content-Type: application/json" -d "{\"keys\":[\"$K\"]}"; echo
curl -s $GW/v1/models -H "Authorization: Bearer $K" | head -c 300; echo
```

**Expect:** the key works first, then the same key is refused. Think: how long would this take if the key were a raw cloud key pasted on six machines?

### Test 2. The request limit

```
K=$(mk_key limited 3)
for i in 1 2 3 4 5 6; do curl -s -o /dev/null -w "call $i -> code %{http_code}\n" $GW/v1/chat/completions -H "Authorization: Bearer $K" -H "Content-Type: application/json" -d '{"model":"team-chat","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'; done
```

**Expect:** the first calls show `200` (success). After 3 in a minute, they show `429` (too many requests).

### Test 3. The budget runs out

```
K=$(mk_key tiny 60 0.0005)
for i in $(seq 1 8); do curl -s -o /dev/null -w "call $i -> code %{http_code}\n" $GW/v1/chat/completions -H "Authorization: Bearer $K" -H "Content-Type: application/json" -d '{"model":"team-chat","messages":[{"role":"user","content":"Write 150 words about mobile towers."}],"max_tokens":200}'; sleep 6; done
```

**Expect:** early calls `200`, later calls fail with a budget error (`400`). It may stop one or two calls late. This only works because `config.yaml` has the prices.

### Test 4. A wrong model name

```
K=$(mk_key typo)
curl -s $GW/v1/chat/completions -H "Authorization: Bearer $K" -H "Content-Type: application/json" -d '{"model":"gpt-4o","messages":[{"role":"user","content":"hi"}]}'; echo
```

**Expect:** a clear refusal message. Copy it word for word.

### Test 5. Fallback (challenge)

Ask your trainer for help the first time. The idea: make the main model unreachable and watch `team-chat-b` answer instead.

### Your results

| Test | What I guessed | What I saw |
|---|---|---|
| 1. Revoked key | | |
| 2. Request limit | | |
| 3. Budget | | |
| 4. Wrong model name | | |

---

## Part 8. Save your work (5 min)

```
cd ~/gateway
printf ".env\n" > .gitignore
git init -q 2>/dev/null
git config user.name "Team" && git config user.email "team@example.com"
git add -A && git commit -qm "Day 1 team gateway" && git tag day1
git log --oneline --decorate | head -3
```

**Expect:** a line that ends with `tag: day1`.

---

## Done check

- [ ] I can log in to `team-vm-a`
- [ ] `curl $GW/health/liveliness` says "I'm alive!"
- [ ] A question to `team-chat` returns an answer
- [ ] Each person has their own key
- [ ] A key made on my gateway works from my lab VM
- [ ] I saw a 429, a revoked key, and a budget stop
- [ ] I can explain in one sentence why a gateway is better than giving everyone the cloud key

## Problems and fixes

| What you see | Likely cause | Fix |
|---|---|---|
| `docker: permission denied` | Login not refreshed | Run `exit`, log in again |
| Install command hangs | No internet on the VM | Tell your trainer |
| `curl` to central gateway times out | Wrong address or network block | Check `CENTRAL_IP`; tell your trainer |
| `401` or "Authentication Error" | Wrong or mistyped key | Copy the key again, with no spaces |
| `Model not found` | Model name typed wrongly | Run `cat config.yaml`; names after `openai/` must match Part 1 |
| Container keeps restarting | Mistake in `config.yaml` | Run `docker compose logs --tail 30 litellm` and read the last lines |
| `export` values are empty | New login clears them | Paste the `export` lines again |
| Answer works but spend shows $0 | Prices missing in `config.yaml` | Check the two `cost_per_token` lines |
| Works on team-vm-a but not from your VM | Port 4000 blocked | Tell your trainer |

**Stuck for more than 10 minutes? Raise your hand and bring the exact error text.**
