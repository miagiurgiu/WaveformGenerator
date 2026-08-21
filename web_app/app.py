import shutil
import tempfile
from pathlib import Path
#.
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from waveform_engine import generate_video


WEB_FOLDER = Path(__file__).resolve().parent

app = FastAPI(
    title="Audio Waveform Generator"
)

app.mount(
    "/static",
    StaticFiles(
        directory=WEB_FOLDER / "static"
    ),
    name="static"
)

templates = Jinja2Templates(
    directory=WEB_FOLDER / "templates"
)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.post("/generate")
def generate(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    color: str = Form(...),
    export_type: str = Form(...)
):
    export_settings = {

        "prores_audio": {
            "extension": ".mov",
            "media_type": "video/quicktime",
            "ending": "_transparent_audio",
        },

        "prores_silent": {
            "extension": ".mov",
            "media_type": "video/quicktime",
            "ending": "_transparent_silent",
        },

        "prores_shorts_audio": {
            "extension": ".mov",
            "media_type": "video/quicktime",
            "ending": "_transparent_shorts_audio",
        },

        "prores_shorts_silent": {
            "extension": ".mov",
            "media_type": "video/quicktime",
            "ending": "_transparent_shorts_silent",
        },
    }

    if export_type not in export_settings:
        raise HTTPException(
            status_code=400,
            detail="Invalid export type."
        )

    settings = export_settings[export_type]

    temporary_folder = Path(
        tempfile.mkdtemp(prefix="waveform_")
    )

    original_name = (
        audio_file.filename or "audio"
    )

    input_extension = (
        Path(original_name).suffix.lower()
        or ".bin"
    )

    input_path = temporary_folder / (
        "input" + input_extension
    )

    output_name = (
        Path(original_name).stem
        + settings["ending"]
        + settings["extension"]
    )

    output_path = temporary_folder / output_name

    try:
        with input_path.open("wb") as destination:
            shutil.copyfileobj(
                audio_file.file,
                destination
            )

        generate_video(
            audio_file=input_path,
            output_file=output_path,
            color=color,
            duration_seconds=None,
            export_type=export_type
        )

    except Exception:
        shutil.rmtree(
            temporary_folder,
            ignore_errors=True
        )
        raise

    finally:
        audio_file.file.close()

    background_tasks.add_task(
        shutil.rmtree,
        temporary_folder,
        ignore_errors=True
    )

    return FileResponse(
        path=output_path,
        media_type=settings["media_type"],
        filename=output_name
    )