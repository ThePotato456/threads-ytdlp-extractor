<p align="center">
  <img src="assets/ascii-art-text.png" alt="Threads.com ASCII logo">
</p>

# yt-dlp Threads Extractor Plugin

Unofficial `yt-dlp` plugin for downloading media from public Threads posts.

## Supported URLs

```text
https://www.threads.net/@username/post/SHORTCODE
https://www.threads.com/@username/post/SHORTCODE
https://www.threads.net/t/SHORTCODE
```

## Installation

Install from GitHub:

```powershell
python -m pip install git+https://github.com/ThePotato456/threads-ytdlp-extractor.git
```

Use `python -m yt_dlp` from the same Python environment so yt-dlp can discover the installed plugin:

```powershell
python -m yt_dlp "https://www.threads.net/@username/post/SHORTCODE"
```

For local development:

```powershell
git clone https://github.com/ThePotato456/threads-ytdlp-extractor.git
cd threads-ytdlp-extractor
python -m pip install -e ".[test]"
```

## Usage

Download a post:

```powershell
python -m yt_dlp "https://www.threads.net/@username/post/SHORTCODE"
```

Preview the extracted result:

```powershell
python -m yt_dlp --simulate --print "%(extractor)s %(id)s %(ext)s" "https://www.threads.net/@username/post/SHORTCODE"
```

Set an output path:

```powershell
python -m yt_dlp -o "downloads\%(id)s.%(ext)s" "https://www.threads.net/@username/post/SHORTCODE"
```

## Graph API Token

The plugin can use the Threads Graph API when an access token is available.

Pass the token with extractor arguments:

```powershell
python -m yt_dlp --extractor-args "threads:access_token=TOKEN" "https://www.threads.net/@username/post/SHORTCODE"
```

Or set an environment variable:

```powershell
$env:THREADS_ACCESS_TOKEN = "TOKEN"
python -m yt_dlp "https://www.threads.net/@username/post/SHORTCODE"
```

## Plugin Directory Mode

You can also run the plugin without installing it:

```powershell
python -m yt_dlp --plugin-dirs .\plugins "https://www.threads.net/@username/post/SHORTCODE"
```

## Testing

```powershell
python -m pip install -e ".[test]"
python -m pytest -q
```

## Requirements

- Python 3.10 or newer
- `yt-dlp`

## Limitations

- Only public, accessible Threads posts are supported.
- Private, deleted, login-gated, or region-restricted posts may not work.
- Threads page data can change without notice.

## License

MIT
