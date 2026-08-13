@echo off
echo ========================================================
echo Force Pushing SmartMeet AI v2 to GitHub (dhanusharer)
echo ========================================================

git init
git add .
git commit -m "Deploy SmartMeet AI v2 - Multi-Agent Intelligence Engine"
git branch -M main
git remote set-url origin https://github.com/dhanusharer/smartmeet-ai.git
git push -u origin main --force

echo ========================================================
echo Done! Code is live on https://github.com/dhanusharer/smartmeet-ai
echo Now go to https://vercel.com/new to deploy in 1 click!
echo ========================================================
pause
