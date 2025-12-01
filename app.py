from pathlib import Path

from flask import Flask, render_template_string, request

from framework_matcher import (
    COLOR_PALETTE,
    gather_files,
    merge_files,
    suggest_frameworks,
)

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8" />
    <title>文件合并</title>
    <style>
        :root {
            --smog-blue: {{ palette["smog_blue"] }};
            --lemon-yellow: {{ palette["lemon_yellow"] }};
            --sunset-red: {{ palette["sunset_red"] }};
        }
        body {
            font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
            margin: 0;
            background: var(--smog-blue);
            color: #fff;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 40px 16px;
        }
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(12px);
            padding: 32px;
            border-radius: 16px;
            max-width: 640px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.35);
        }
        h1 {
            margin-top: 0;
            color: var(--lemon-yellow);
        }
        label {
            display: block;
            margin-top: 20px;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 10px 14px;
            border: none;
            border-radius: 8px;
            margin-top: 8px;
            font-size: 1rem;
        }
        button {
            margin-top: 28px;
            width: 100%;
            padding: 12px;
            font-size: 1.1rem;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            background: var(--sunset-red);
            color: #fff;
            font-weight: 700;
            transition: transform 0.2s ease;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .result {
            margin-top: 28px;
            padding: 20px;
            border-radius: 12px;
            background: rgba(0, 0, 0, 0.35);
        }
        .error {
            margin-top: 16px;
            color: var(--sunset-red);
            font-weight: 600;
        }
        ul {
            padding-left: 18px;
        }
        .palette {
            display: flex;
            gap: 12px;
            margin-top: 16px;
        }
        .swatch {
            flex: 1;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            font-weight: 600;
        }
    </style>
</head>
<body>
<div class="card">
    <h1>文件合并</h1>
    <p>选择一个文件后缀，合并指定目录内的所有文件。</p>
    <form method="post">
        <label>根目录 (默认当前目录)
            <input type="text" name="root" value="{{ form.root or '' }}" placeholder="例如：C:\\\\projects\\\\site" />
        </label>
        <label>文件后缀（必填）
            <input type="text" name="extension" value="{{ form.extension or '' }}" placeholder=".vue / .js / .ts ..." required />
        </label>
        <label>输出文件（可选）
            <input type="text" name="output" value="{{ form.output or '' }}" placeholder="例如：C:\\\\temp\\\\merged.vue" />
        </label>
        <button type="submit">开始分析</button>
    </form>

    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}

    {% if result %}
        <div class="result">
            <h2>结果</h2>
            <p>已合并 <strong>{{ result.count }}</strong> 个文件，输出至：</p>
            <p><code>{{ result.output }}</code></p>
            <h3>推荐框架</h3>
            <ul>
                {% for hint in result.hints %}
                    <li><strong>{{ hint.name }}</strong> - {{ hint.reason }}</li>
                {% endfor %}
            </ul>
            <h3>配色</h3>
            <div class="palette">
                {% for label, hex_code in palette.items() %}
                    <div class="swatch" style="background: {{ hex_code }};">
                        {{ label }}<br/>{{ hex_code }}
                    </div>
                {% endfor %}
            </div>
        </div>
    {% endif %}
</div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    result = None
    form_state = {
        "root": request.form.get("root", "") if request.method == "POST" else "",
        "extension": request.form.get("extension", "") if request.method == "POST" else "",
        "output": request.form.get("output", "") if request.method == "POST" else "",
    }

    if request.method == "POST":
        root_input = form_state["root"].strip() or "."
        extension = form_state["extension"].strip()
        output_input = form_state["output"].strip()

        if not extension:
            error = "请填写文件后缀，例如 .vue 或 .js"
        else:
            try:
                root_path = Path(root_input).expanduser().resolve()
                output_path = Path(output_input).expanduser().resolve() if output_input else (
                        root_path / f"combined{normalize_extension(extension)}"
                )

                files = gather_files(root_path, extension)
                if not files:
                    error = "未在指定目录找到匹配文件。"
                else:
                    merged = merge_files(files, output_path)
                    hints = suggest_frameworks(extension)
                    result = {
                        "count": len(files),
                        "output": str(merged),
                        "hints": hints,
                    }
            except Exception as exc:
                error = str(exc)

    return render_template_string(
        TEMPLATE,
        palette=COLOR_PALETTE,
        result=result,
        error=error,
        form=form_state,
    )


def normalize_extension(extension: str) -> str:
    extension = extension.strip()
    return extension if extension.startswith(".") else f".{extension}"


if __name__ == "__main__":
    app.run(debug=True)

