# AutoGG

AutoGG is a Flask-based Google Forms auto-filler that uses Selenium with Chrome to submit randomized responses through a small web UI.

## What It Does

- Opens a Google Form in Chrome
- Detects supported question types
- Generates randomized answers
- Submits the form one or more times
- Shows success, failure, and timing results in the browser

## Supported Question Types

- Radio / multiple choice
- Checkboxes
- Dropdowns
- Short text
- Long text
- Linear scale
- Grid

## Requirements

- Python 3.10+
- Google Chrome installed
- Internet access to load the target Google Form

Python dependencies are listed in `requirements.txt`.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run The App

Start the Flask server:

```powershell
python auto.py
```

By default, the app starts at:

```text
http://127.0.0.1:5000
```

Open that URL in your browser, then:

1. Paste a Google Forms URL.
2. Enter the number of submissions to run.
3. Choose whether Chrome should run headless.
4. Submit the form.

## Configuration

The app reads settings from environment variables.

| Variable | Default | Description |
| --- | --- | --- |
| `AUTOGG_HEADLESS` | `true` | Run Chrome in headless mode by default |
| `AUTOGG_INCOGNITO` | `true` | Start Chrome in incognito mode |
| `AUTOGG_DISABLE_EXTENSIONS` | `true` | Disable Chrome extensions |
| `AUTOGG_DISABLE_INFOBARS` | `true` | Disable Chrome infobars |
| `AUTOGG_START_MAXIMIZED` | `true` | Start Chrome maximized |
| `AUTOGG_PAGE_LOAD_TIMEOUT` | `30` | Page load timeout in seconds |
| `AUTOGG_WAIT_TIMEOUT` | `10` | Selenium wait timeout in seconds |
| `AUTOGG_MAX_WORKERS` | `1` | Maximum worker threads for submissions |
| `AUTOGG_ENABLE_PROFILING` | `false` | Enable per-submission profiling logs |
| `AUTOGG_PROFILE_OUTPUT_DIR` | `profiles` | Reserved profile output directory setting |
| `AUTOGG_HOST` | `127.0.0.1` | Flask host |
| `AUTOGG_PORT` | `5000` | Flask port |
| `AUTOGG_SECRET_KEY` | `autogg-dev` | Flask secret key |
| `AUTOGG_CHROME_BINARY` | unset | Custom Chrome binary path |
| `AUTOGG_CHROMEDRIVER` | unset | Custom ChromeDriver path |

Example:

```powershell
$env:AUTOGG_HEADLESS = "false"
$env:AUTOGG_MAX_WORKERS = "2"
python auto.py
```

## How ChromeDriver Works

If `AUTOGG_CHROMEDRIVER` is set, AutoGG uses that executable path.

If it is not set, Selenium will use its normal Chrome driver resolution flow. In most setups this means Selenium Manager can locate or fetch a compatible driver automatically.

## Validation Rules

The web UI currently accepts:

- Only `http` or `https` URLs
- Only `docs.google.com` URLs
- Only URLs whose path contains `/forms/`
- Only positive integer submission counts

## Run Tests

```powershell
pytest
```

The test suite covers config parsing, browser lifecycle, parser behavior, strategy generation, form filling flow, and Flask routes.

## Project Structure

```text
autogg/
|-- app/
|   |-- __init__.py
|   |-- browser.py
|   |-- config.py
|   |-- form_filler.py
|   |-- form_parser.py
|   |-- routes.py
|   `-- strategy.py
|-- static/
|   `-- style.css
|-- templates/
|   |-- index.html
|   `-- result.html
|-- tests/
|   |-- conftest.py
|   |-- test_browser.py
|   |-- test_config.py
|   |-- test_form_filler.py
|   |-- test_form_parser.py
|   |-- test_routes.py
|   `-- test_strategy.py
|-- auto.py
|-- pytest.ini
|-- README.md
`-- requirements.txt
```

## Limitations

- Google Forms markup can change, which may require selector updates
- Forms requiring sign-in, CAPTCHA, or strict anti-bot checks may fail
- The tool is designed for Chrome only
- The current strategy is random only; it does not support fixed answer templates

## Development Notes

- `auto.py` is only the Flask entry point
- Browser lifecycle is handled in `app/browser.py`
- Question detection is handled in `app/form_parser.py`
- Submission orchestration is handled in `app/form_filler.py`
- Random answer generation is handled in `app/strategy.py`

