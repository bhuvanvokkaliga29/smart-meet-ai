@echo off
echo ========================================================
echo Pushing SmartMeet AI v2 to GitHub
echo ========================================================

git add .
git commit -m "feat: vercel deployment configuration, comprehensive enterprise architecture diagrams, and resilient demo pipeline"
git push origin main

echo ========================================================
echo Done! Code is pushed to GitHub.
echo Connect your repo to Vercel at https://vercel.com/new
echo ========================================================
pause
