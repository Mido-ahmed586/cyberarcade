# Screenshots

Place platform screenshots in this directory. The following filenames are referenced in the main README:

| File | Page |
|---|---|
| `landing.png` | Landing / home page |
| `dashboard.png` | Student dashboard |
| `courses.png` | Course catalog |
| `lab.png` | Live lab terminal environment |
| `ai-coach.png` | AI Cybersecurity Coach |
| `instructor.png` | Instructor dashboard |
| `leaderboard.png` | Leaderboard |
| `admin.png` | Admin panel |

## Recommended Capture Settings

- **Resolution:** 1920×1080 (full HD)
- **Format:** PNG
- **Browser:** Chrome or Firefox, zoom at 100%
- **Theme:** Dark mode (matches platform default)

## Quick Capture Checklist

1. Start the platform: `docker compose up -d`
2. Seed the database: `docker exec cyberarcade-backend-1 python seeds/seed_all.py`
3. Navigate to each page and capture with your preferred screenshot tool
4. Name files exactly as listed in the table above
5. Place them in this directory

The README will display them automatically once the files exist.
