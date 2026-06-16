# Deployment V2 Local Streamlit Quick-Start Checklist

## Purpose

This is the one-page V1 local-only quick-start for a non-technical operator. It
helps an operator start the Niners War Room Streamlit app on their own computer.

This checklist is not hosted deployment approval. It does not create a deploy
command, public app, public port, tunnel, secret, container, or CI/CD workflow.

## Use The Right Folder

HQ has not selected the normal long-term operator repo/worktree path yet.

Until HQ selects one, use the path HQ gives you for that session. The expected
path should look like a Niners War Room repo folder, for example:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2
```

If you are not sure which folder to use, stop and ask HQ before running the app.

## Start Checklist

1. Open PowerShell.
2. Go to the folder HQ told you to use:

   ```powershell
   Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2"
   ```

3. Confirm you are in the right folder:

   ```powershell
   git rev-parse --show-toplevel
   ```

   The output should be the same folder HQ told you to use.

4. If `.venv` is missing, create it:

   ```powershell
   python -m venv .venv
   ```

5. Activate `.venv`:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

6. Confirm `.venv` is active. PowerShell should show `(.venv)` at the start of
   the prompt.

7. Install the documented dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

8. Start the local app:

   ```powershell
   streamlit run app/main.py
   ```

## What Success Looks Like

After startup, Streamlit normally prints local URLs in the terminal. The output
should look similar to:

```text
Local URL: http://localhost:8501
Network URL: http://...
```

Use only the local URL. Do not share or publish the app.

Open the Rankings page at:

```text
http://localhost:8501/rankings
```

If Streamlit uses a different local port, use the port shown in the terminal and
add `/rankings`. For example:

```text
http://localhost:8502/rankings
```

## Rankings Page Checks

On Rankings, confirm the Outcome columns appear only where approved.

Approved Outcome numeric heads:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

These should not appear:

- Top 6
- unapproved heads
- sorting or ranking changes caused by Outcome columns
- hidden sort keys

Data readiness is separate from app startup readiness. The app can start even if
the selected local data pack still needs review.

## Stop And Restart

To stop the local app, click in the PowerShell window running Streamlit and press:

```text
Ctrl+C
```

To restart, run:

```powershell
streamlit run app/main.py
```

If the normal port is already busy, Streamlit may choose another local port. Use
the local URL printed in the terminal. Do not open a public port, tunnel, or
hosted share.

## Do Not Commit Local Files

Do not commit these folders:

- `.venv/`
- `data/`
- `local_exports/`

This checklist is for local operation only. Hosted deployment remains blocked.
