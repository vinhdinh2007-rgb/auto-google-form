# AutoGG

A Flask-based web application that automates Google Form submissions using Selenium and Chrome.

## Features

- Accepts a Google Forms URL and number of submissions
- Supports headless and non-headless Chrome modes
- Handles multiple Google Form question types: radio buttons, checkboxes, dropdowns, short/long text, and grid scales
- Randomized answer generation for each submission

## Tech Stack

- **Backend**: Python 3 with Flask
- **Automation**: Selenium with Google Chrome/ChromeDriver
- **Templates**: Jinja2 HTML templates
- **Production server**: Gunicorn

## UI Design

The UI uses an anime-themed "Hanabi/Sparkle" design with:
- Dark fireworks wallpaper background (Unsplash image)
- Floating anime character (Hanabi) on the left side (large screens)
- Neo-brutalist main card with rose/pink color scheme, thick borders, pill-shaped elements
- Floating decorative SVG icons (flame, star, ghost) with CSS animations
- Nunito rounded font
- Playful copy ("Let's play a game!", "Ignite the Fireworks!", etc.)
- Reduced motion support via prefers-reduced-motion media query
- Accessible decorative elements with aria-hidden

## Project Structure

```
autogg/
├── app/                  # Core application logic
│   ├── __init__.py       # Flask app factory (create_app)
│   ├── browser.py        # Selenium WebDriver lifecycle
│   ├── config.py         # Configuration (dataclasses + env vars)
│   ├── form_filler.py    # Orchestrates form submission
│   ├── form_parser.py    # Google Form question type detection
│   ├── routes.py         # Flask Blueprints and URL routing
│   └── strategy.py       # Randomized answer generation
├── static/               # Static assets (CSS, images)
│   ├── style.css         # Main stylesheet (anime theme)
│   └── hanabi.png        # Anime character image
├── templates/            # Jinja2 HTML templates
│   ├── index.html        # Main form page
│   └── result.html       # Results display page
├── tests/                # pytest test suite
├── auto.py               # Entry point (Flask dev server)
└── requirements.txt      # Python dependencies
```

## Configuration

Environment variables (all prefixed with `AUTOGG_`):

- `AUTOGG_HEADLESS` - Run Chrome headlessly (default: true)
- `AUTOGG_INCOGNITO` - Use incognito mode (default: true)
- `AUTOGG_MAX_WORKERS` - Max concurrent form submissions (default: 1)
- `AUTOGG_PAGE_LOAD_TIMEOUT` - Page load timeout in seconds (default: 30)
- `AUTOGG_WAIT_TIMEOUT` - Element wait timeout (default: 10)
- `AUTOGG_SECRET_KEY` - Flask secret key (default: "autogg-dev")
- `AUTOGG_CHROME_BINARY` - Path to Chrome binary (optional)
- `AUTOGG_CHROMEDRIVER` - Path to ChromeDriver (optional)

## Running

The app runs on port 5000 via:
```
python auto.py
```

## Deployment

Configured for autoscale deployment using gunicorn:
```
gunicorn --bind=0.0.0.0:5000 --reuse-port auto:app
```
