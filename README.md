# Media Radar - AI Media Creator Coach 🎬🤖

**Media Radar Coach** is an autonomous AI agent designed for video editors and content creators. It audits social profile analytics, tracks performance metrics over time, and delivers twice-daily direct, punchy, and actionable video editing and media strategy advice to Discord channel.

---

## 🌟 Key Features

- **📊 Profile Analytics (`MediaAnalyst`)**: Automatically audits recent video metrics (`views`, `likes`, `comments`, `engagement rate`) using browser impersonation and rehydration data.
- **🧠 Long-Term Memory & Compaction (`HistoryManager`)**: Retains a 50-session conversation thread in `services/coach_service/data/history.json` with automatic context compaction for long-term memory.
- **🤖 Senior Editor Intelligence (`AICreatorCoach`)**: Powered by **Google Gemini 3.6 Flash**. Provides **exactly 2 concise, actionable methods** per check-in for performance improvement with strict, non-flattering encouragement.
- **💬 Direct Discord Integration (`DiscordPoster`)**: Sends organic, fluid Markdown messages directly to Discord channel twice daily (Morning & Evening) via Webhook.

---

## 📁 Architecture Overview

```
services/coach_service/
├── config.py                 # Service environment configuration
├── config/
│   └── prompts.json          # System instructions & prompt templates
├── analytics/
│   └── media_analyst.py      # Profile & video metrics extraction
├── intelligence/
│   └── ai_coach.py           # Gemini LLM integration & report generation
├── storage/
│   └── history_manager.py    # Long-term thread memory & compaction
├── publishers/
│   └── discord_publisher.py  # Discord Webhook publisher (Radar-01 avatar)
├── data/
│   └── history.json          # Persistent report snapshots & memory log
└── main.py                   # Main CLI entry point
```

---

## ⚙️ Environment Configuration

Create or update your `.env` file in the project root:

```env
# Coach Service Configuration
DISCORD_COACH_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/COACH/WEBHOOK
PROFILE_URL=https://www.tiktok.com/@your_username
GEMINI_COACH_API_KEY=your_gemini_api_key
```

---

## 🚀 Usage & Testing

### Run Local Dry-Run (No Discord Webhooks sent)
```bash
./venv/bin/python services/coach_service/main.py --dry-run
```

### Run Live Execution
```bash
./venv/bin/python services/coach_service/main.py
```

---

## ⏰ Automated Schedule

The service runs twice daily via GitHub Actions (`.github/workflows/coach_poster.yml`):
- **Morning Check-in**: ~08:00 UTC
- **Evening Check-in**: ~18:00 UTC
