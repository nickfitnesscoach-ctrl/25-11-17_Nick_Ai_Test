#!/bin/bash
cd /root/bots/25-11-17_Nick_Ai_Test
git pull
docker compose up -d --build bot
docker compose logs --tail=50 bot
