# Lab 5 — Deploy AskNova to the Cloud: Azure and AWS (90 min)

**Goal:** the same code that runs on your VM now runs on a public URL. No code change.

```
 your VM (laptop)                     Azure App Service (managed)          AWS EC2 (a server you manage)
 streamlit run app.py   --->   az webapp up  (Azure builds + runs it)   git clone + systemd service
 key typed in sidebar          key in App settings (env var)            key in /etc/asknova.env (env var)
```

| | Azure App Service | AWS EC2 |
|---|---|---|
| Type | PaaS: Azure runs the server for you | IaaS: you get a Linux server |
| You manage | only your code | OS, Python, updates, restarts |
| Deploy with | 1 command (`az webapp up`) | ~10 commands |
| Good for | most web apps and agents | full control, custom software |

**Security rules for both:**
- the key is **never in the code or git**: it goes in a server environment variable
- the app is protected with a password (`APP_PASSWORD`)
- delete everything at the end (cost!)

You got a login from your trainer for **one Azure resource group** and **one AWS user**. Use only those.

---

## Part A — Azure App Service (40 min)

We use **Azure Cloud Shell**: a terminal in the browser with `az` and `git` already installed.

| # | Where | Command / action | You should see |
|---|---|---|---|
| 1 | Browser | open https://portal.azure.com, sign in with the login you were given | Azure portal |
| 2 | Portal | click the **Cloud Shell** icon `>_` (top bar), choose **Bash**, "No storage account" if asked | a terminal at the bottom |
| 3 | Cloud Shell | `git clone https://github.com/askanilkumar/kyndryl-aidevs.git` | repo is cloned (private repo? see note below) |
| 4 | Cloud Shell | `cd kyndryl-aidevs/day5/Labs` | — |
| 5 | Cloud Shell | `NAME=asknova-<yourname>`  then  `RG=<resource group from trainer>` | — (use small letters, no spaces) |
| 6 | Cloud Shell | `az webapp up --name $NAME --resource-group $RG --runtime "PYTHON:3.12" --sku B1 --location centralindia` | after 3-5 min: JSON with `"URL": "http://asknova-....azurewebsites.net"` |
| 7 | Cloud Shell | `az webapp config set --name $NAME --resource-group $RG --web-sockets-enabled true --startup-file "python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true"` | JSON output |
| 8 | Cloud Shell | `read -s -p "OpenAI key: " KEY; echo` then paste the key, press Enter | nothing is shown (good: the key is not in history) |
| 9 | Cloud Shell | `az webapp config appsettings set --name $NAME --resource-group $RG --settings OPENAI_API_KEY="$KEY" APP_PASSWORD="<pick a password>"` | JSON list of settings |
| 10 | Browser | open `https://$NAME.azurewebsites.net` (first load takes ~1 min) | AskNova asks for the password |
| 11 | AskNova | log in, ask `What is the status of INC-5001?` | sidebar says `Mode: OpenAI`, answer comes back |
| 12 | Cloud Shell | `az webapp log tail --name $NAME --resource-group $RG` (Ctrl+C to stop) | Streamlit log lines live from Azure |

**Private repo?** In step 3 use `git clone https://<your-github-token>@github.com/askanilkumar/kyndryl-aidevs.git`, or zip the `day5/Labs` folder on your VM and upload it with Cloud Shell **Manage files → Upload**, then `unzip Labs.zip`.

**If the page shows "Application Error":** run step 12 and read the last lines. Most common: a typo in the startup command (step 7) or `requirements.txt` not found (you were not inside `day5/Labs` in step 6).

---

## Part B — AWS EC2 (40 min)

| # | Where | Command / action | You should see |
|---|---|---|---|
| 1 | Browser | sign in to https://console.aws.amazon.com with the login you were given; region (top right) **Asia Pacific (Mumbai) ap-south-1** | AWS console |
| 2 | EC2 → **Launch instance** | Name `asknova-<yourname>`, AMI **Ubuntu Server 24.04 LTS**, type **t3.small**, Key pair **Proceed without a key pair** | — |
| 3 | Launch → Network settings → **Edit** | Create security group. Rule 1: **SSH**, source **Custom**, type `ec2-instance-connect` and pick the `com.amazonaws.ap-south-1.ec2-instance-connect` list | only AWS's browser terminal can SSH in |
| 4 | same screen | **Add rule**: Custom TCP, port **8501**, source **My IP** | only your VM can open the app |
| 5 | Launch | click **Launch instance**, wait for **Running** (1-2 min) | instance with a Public IPv4 address |
| 6 | Instance → **Connect** | tab **EC2 Instance Connect**, user `ubuntu`, **Connect** | a Linux terminal in the browser |
| 7 | EC2 terminal | `sudo apt update && sudo apt install -y python3-venv git` | packages installed |
| 8 | EC2 terminal | `git clone https://github.com/askanilkumar/kyndryl-aidevs.git && cp -r kyndryl-aidevs/day5/Labs ~/asknova && cd ~/asknova` | — |
| 9 | EC2 terminal | `python3 -m venv ~/venv && ~/venv/bin/pip install -r requirements.txt` | installs finish |
| 10 | EC2 terminal | `~/venv/bin/python check_setup.py` | 6 × `ok` |
| 11 | EC2 terminal | `sudo nano /etc/asknova.env` and type 2 lines: `OPENAI_API_KEY=sk-...` and `APP_PASSWORD=<pick a password>`. Save: Ctrl+O, Enter, Ctrl+X | — |
| 12 | EC2 terminal | `sudo chmod 600 /etc/asknova.env` | only root can read the key file |
| 13 | EC2 terminal | `sudo cp deploy/asknova.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now asknova` | no output = good |
| 14 | EC2 terminal | `systemctl status asknova` | `active (running)` (press `q` to exit) |
| 15 | Browser on your VM | open `http://<Public IPv4>:8501` | AskNova asks for the password |
| 16 | AskNova | log in and ask a question | `Mode: OpenAI`, answer comes back |
| 17 | EC2 terminal | `sudo reboot`, wait 1 min, open the URL again | the app is back by itself (that is what systemd gives you) |
| 18 | EC2 terminal | `journalctl -u asknova -n 30` | the app's log lines |

Why `/etc/asknova.env` and not a file in `~/asknova`? Because `~/asknova` is your git folder. Anything in it can be pushed to GitHub by mistake.

---

## Solo / discussion (10 min)
Fill this table in `submission/notes.md`:

| Question | Azure App Service | AWS EC2 |
|---|---|---|
| How many commands to deploy? | | |
| Who patches the OS? | | |
| How do you deploy a new version? | | |
| Where is the key stored? Is that good enough for production? | | |
| What would you add for production? (HTTPS, Key Vault / Secrets Manager, scaling, CI/CD, private network) | | |

## Clean up (5 min) — do not skip
| Cloud | Do this |
|---|---|
| Azure | Cloud Shell: `az webapp delete --name $NAME --resource-group $RG` and `az appservice plan list -g $RG -o table`, then delete the plan: `az appservice plan delete --name <plan name> --resource-group $RG --yes` |
| AWS | EC2 → Instances → select yours → **Instance state → Terminate**. Then delete the security group. |

**Remember:** deploying is not the end. In production you add HTTPS, a secret store, CI/CD from git, and the Lab 2-3 tracing and monitoring keep running on the live app.
