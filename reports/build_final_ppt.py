import json
import math
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
CONTENT_PATH = REPORT_DIR / "final_report_content.json"
PPTX_PATH = REPORT_DIR / "gesture_control_system_final_report.pptx"
SCRIPT_PATH = REPORT_DIR / "gesture_control_system_speaker_notes.md"
COVER_IMAGE = REPORT_DIR / "assets" / "gesture_cover.png"

SLIDE_W = 1280
SLIDE_H = 720
EMU_PER_PX = 9525

COLORS = {
    "bg": "F7F9FC",
    "ink": "20242A",
    "muted": "69707A",
    "primary": "F08A24",
    "secondary": "1565C0",
    "green": "2F9E44",
    "card": "FFFFFF",
    "line": "D9E1EA",
    "dark": "18212B",
}


def emu(value):
    return int(value * EMU_PER_PX)


def xesc(text):
    return escape(str(text), {'"': "&quot;"})


def paragraphs(lines, size=24, color=None, bold=False, bullet=False):
    out = []
    for line in lines:
        line = str(line)
        mar = ' marL="285750" indent="-171450"' if bullet else ""
        bu = '<a:buChar char="•"/>' if bullet else "<a:buNone/>"
        bold_attr = 'b="1"' if bold else ""
        out.append(
            f'<a:p><a:pPr{mar}>{bu}</a:pPr>'
            f'<a:r><a:rPr lang="zh-TW" sz="{size * 100}" {bold_attr}>'
            f'<a:solidFill><a:srgbClr val="{color or COLORS["ink"]}"/></a:solidFill>'
            f'<a:latin typeface="Microsoft JhengHei"/><a:ea typeface="Microsoft JhengHei"/>'
            f'</a:rPr><a:t>{xesc(line)}</a:t></a:r></a:p>'
        )
    return "".join(out)


def text_box(shape_id, x, y, w, h, lines, size=24, color=None, bold=False, bullet=False, align=None):
    body = paragraphs(lines if isinstance(lines, list) else [lines], size, color, bold, bullet)
    align_xml = f' algn="{align}"' if align else ""
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{shape_id}" name="TextBox {shape_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        <a:noFill/><a:ln><a:noFill/></a:ln>
      </p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square" anchor="t"/>
        <a:lstStyle/>
        {body}
      </p:txBody>
    </p:sp>
    """


def rect(shape_id, x, y, w, h, fill, line=None, radius=False):
    prst = "roundRect" if radius else "rect"
    ln = (
        f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
        if line else '<a:ln><a:noFill/></a:ln>'
    )
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{shape_id}" name="Shape {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
        <a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>
        <a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>
        {ln}
      </p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
    </p:sp>
    """


def line(shape_id, x1, y1, x2, y2, color="D9E1EA", width=2):
    return f"""
    <p:cxnSp>
      <p:nvCxnSpPr><p:cNvPr id="{shape_id}" name="Line {shape_id}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{emu(min(x1, x2))}" y="{emu(min(y1, y2))}"/><a:ext cx="{emu(abs(x2 - x1))}" cy="{emu(abs(y2 - y1))}"/></a:xfrm>
        <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
        <a:ln w="{width * 12700}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:ln>
      </p:spPr>
    </p:cxnSp>
    """


def image_pic(shape_id, rel_id, x, y, w, h):
    return f"""
    <p:pic>
      <p:nvPicPr><p:cNvPr id="{shape_id}" name="Cover Image"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr>
        <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
      </p:spPr>
    </p:pic>
    """


def footer(slide_no, total):
    return (
        rect(9900 + slide_no, 40, 674, 1200, 1, COLORS["line"])
        + text_box(10000 + slide_no, 44, 680, 480, 24, "Gesture Control System", 11, COLORS["muted"])
        + text_box(10100 + slide_no, 1140, 680, 100, 24, f"{slide_no:02d}/{total:02d}", 11, COLORS["muted"], align="r")
    )


def slide_xml(shapes):
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="{COLORS["bg"]}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {shapes}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def title_slide(data):
    shapes = ""
    shapes += rect(2, 0, 0, 1280, 720, COLORS["dark"])
    shapes += image_pic(3, "rId2", 545, 0, 735, 720)
    shapes += rect(4, 0, 0, 640, 720, COLORS["dark"])
    shapes += rect(5, 50, 76, 78, 8, COLORS["primary"])
    shapes += text_box(6, 50, 106, 520, 138, data["deck_title"], 42, "FFFFFF", True)
    shapes += text_box(7, 53, 258, 520, 70, data["subtitle"], 20, "E8EDF2")
    shapes += text_box(8, 54, 392, 500, 112, ["期末專題報告", "Python / OpenCV / MediaPipe / Flask / Socket.IO"], 22, "FFFFFF", False)
    shapes += text_box(9, 54, 610, 420, 40, "依評分規範整理：技術、成果、問答、分工", 15, "F7C78F")
    return slide_xml(shapes), True


def diagram_slide(slide, idx, total):
    shapes = ""
    shapes += text_box(2, 54, 34, 850, 56, slide["title"], 34, COLORS["ink"], True)
    shapes += text_box(3, 56, 88, 420, 24, slide["tag"], 14, COLORS["primary"], True)
    nodes = slide.get("diagram", [])
    x0, y = 82, 300
    gap = 28
    box_w = 190
    for i, node in enumerate(nodes):
        x = x0 + i * (box_w + gap)
        shapes += rect(20 + i, x, y, box_w, 86, COLORS["card"], COLORS["line"], True)
        shapes += text_box(40 + i, x + 14, y + 24, box_w - 28, 34, node, 20, COLORS["ink"], True, align="ctr")
        if i < len(nodes) - 1:
            shapes += line(70 + i, x + box_w + 3, y + 43, x + box_w + gap - 5, y + 43, COLORS["primary"], 3)
            shapes += text_box(80 + i, x + box_w + 6, y + 20, 25, 28, "→", 22, COLORS["primary"], True)
    shapes += bullet_area(slide["bullets"])
    shapes += footer(idx, total)
    return slide_xml(shapes), False


def bullet_area(bullets):
    shapes = ""
    y = 140
    shapes += rect(100, 54, 130, 460, 410, COLORS["card"], COLORS["line"], True)
    shapes += text_box(101, 84, y + 18, 400, 350, bullets, 20, COLORS["ink"], False, True)
    return shapes


def standard_slide(slide, idx, total):
    shapes = ""
    shapes += text_box(2, 54, 34, 900, 56, slide["title"], 34, COLORS["ink"], True)
    shapes += text_box(3, 56, 88, 480, 24, slide["tag"], 14, COLORS["primary"], True)

    bullets = slide["bullets"]
    if slide["tag"] == "Q&A":
        shapes += rect(10, 54, 140, 330, 390, "FFF3E6", COLORS["primary"], True)
        shapes += text_box(11, 82, 172, 270, 140, "可能被問", 30, COLORS["primary"], True, align="ctr")
        shapes += text_box(12, 82, 310, 270, 130, slide["title"].replace("可能問題 ", "Q"), 24, COLORS["ink"], True, align="ctr")
        shapes += rect(20, 430, 140, 770, 390, COLORS["card"], COLORS["line"], True)
        shapes += text_box(21, 470, 178, 690, 310, bullets, 22, COLORS["ink"], False, True)
    elif slide["tag"] in {"實驗結果", "問題解決", "團隊分工"}:
        col_w = 270
        for i, b in enumerate(bullets[:4]):
            x = 60 + i * 300
            shapes += rect(20 + i, x, 166, col_w, 250, COLORS["card"], COLORS["line"], True)
            shapes += text_box(40 + i, x + 24, 192, 70, 60, f"{i + 1}", 40, COLORS["primary"], True)
            shapes += text_box(50 + i, x + 24, 270, col_w - 48, 110, b, 20, COLORS["ink"], True)
        if len(bullets) > 4:
            shapes += text_box(70, 70, 460, 1080, 70, bullets[4:], 20, COLORS["ink"], False, True)
    else:
        shapes += rect(10, 58, 150, 525, 400, COLORS["card"], COLORS["line"], True)
        shapes += text_box(11, 92, 188, 465, 320, bullets, 23, COLORS["ink"], False, True)
        shapes += rect(20, 650, 150, 500, 400, "EEF3F7", COLORS["line"], True)
        shapes += text_box(21, 690, 200, 420, 260, slide["notes"], 20, COLORS["muted"])
    shapes += footer(idx, total)
    return slide_xml(shapes), False


def appendix_slide(title, tag, points, idx, total):
    shapes = ""
    shapes += text_box(2, 54, 34, 900, 56, title, 32, COLORS["ink"], True)
    shapes += text_box(3, 56, 88, 480, 24, tag, 14, COLORS["primary"], True)
    y = 132
    for i, p in enumerate(points):
        h = 64 if len(p) < 38 else 88
        shapes += rect(20 + i, 70, y, 1140, h, COLORS["card"], COLORS["line"], True)
        shapes += text_box(50 + i, 94, y + 16, 1080, h - 24, p, 18, COLORS["ink"])
        y += h + 12
        if y > 620:
            break
    shapes += footer(idx, total)
    return slide_xml(shapes), False


def content_types(slide_count, image_count):
    slide_overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, slide_count + 1)
    )
    png_default = '<Default Extension="png" ContentType="image/png"/>' if image_count else ""
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  {png_default}
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  {slide_overrides}
</Types>"""


def rels_root():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def presentation_xml(slide_count):
    ids = "\n".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i + 1}"/>' for i in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>{ids}</p:sldIdLst>
  <p:sldSz cx="{emu(SLIDE_W)}" cy="{emu(SLIDE_H)}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""


def presentation_rels(slide_count):
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    for i in range(1, slide_count + 1):
        rels.append(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>')
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {"".join(rels)}
</Relationships>"""


def master_xml():
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""


def layout_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""


def theme_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Gesture Theme">
  <a:themeElements>
    <a:clrScheme name="Gesture"><a:dk1><a:srgbClr val="20242A"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="18212B"/></a:dk2><a:lt2><a:srgbClr val="F7F9FC"/></a:lt2><a:accent1><a:srgbClr val="F08A24"/></a:accent1><a:accent2><a:srgbClr val="1565C0"/></a:accent2><a:accent3><a:srgbClr val="2F9E44"/></a:accent3><a:accent4><a:srgbClr val="69707A"/></a:accent4><a:accent5><a:srgbClr val="D9E1EA"/></a:accent5><a:accent6><a:srgbClr val="FFF3E6"/></a:accent6><a:hlink><a:srgbClr val="1565C0"/></a:hlink><a:folHlink><a:srgbClr val="69707A"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="Gesture"><a:majorFont><a:latin typeface="Microsoft JhengHei"/><a:ea typeface="Microsoft JhengHei"/></a:majorFont><a:minorFont><a:latin typeface="Microsoft JhengHei"/><a:ea typeface="Microsoft JhengHei"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Gesture"><a:fillStyleLst/><a:lnStyleLst/><a:effectStyleLst/><a:bgFillStyleLst/></a:fmtScheme>
  </a:themeElements>
</a:theme>"""


def slide_rels(has_cover=False):
    rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>']
    if has_cover:
        rels.append('<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/gesture_cover.png"/>')
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(rels)}</Relationships>"""


def static_props(slide_count):
    core = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Gesture Control System 期末報告</dc:title><dc:creator>Codex</dc:creator>
</cp:coreProperties>"""
    app = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft PowerPoint</Application><PresentationFormat>On-screen Show (16:9)</PresentationFormat><Slides>{slide_count}</Slides>
</Properties>"""
    return core, app


def write_notes(data):
    lines = [
        "# Gesture Control System 期末報告文字稿",
        "",
        "## 使用方式",
        "- PPT 用於正式報告。",
        "- 本文字稿包含逐頁講稿、可能問題與回答、程式碼分區註解文字稿。",
        "- 報告時建議先講主流程，再講技術分區，最後用 Q&A 收尾。",
        "",
        "## 逐頁講稿",
        "",
    ]
    for i, s in enumerate(data["slides"], 1):
        lines += [f"### Slide {i:02d}｜{s['title']}", "", s["notes"], ""]
    lines += ["## 程式碼分區註解文字稿", ""]
    for section in data["code_sections"]:
        lines += [f"### {section['name']}", ""]
        for p in section["points"]:
            lines.append(f"- {p}")
        lines.append("")
    lines += [
        "## 可能問答總整理",
        "",
        "### Q1：為什麼不用深度學習模型分類所有手勢？",
        "A：目前手勢種類有限，使用 landmarks 幾何規則即可達成，延遲低、可解釋、容易調整。未來若要擴充更多手勢，才適合加入訓練模型。",
        "",
        "### Q2：如何避免誤觸？",
        "A：系統使用冷卻時間、模式切換停留判斷、滑鼠 deadzone，以及兩段式 OK 確認，避免手勢連續觸發或直接送出訂單。",
        "",
        "### Q3：MediaPipe 如果在不同電腦跑不起來怎麼辦？",
        "A：建議統一 Python 3.11 與 requirements.txt 版本；系統也設計了 Tasks、Solutions 與 OpenCV fallback，降低展示失敗風險。",
        "",
        "### Q4：為什麼確認餐點不用握拳？",
        "A：實測握拳敏感度較不穩，OK 手勢在視覺上也更符合確認語意，因此改成 OK 兩段式確認。",
        "",
        "### Q5：這個系統的限制是什麼？",
        "A：光線、背景、手部遮擋都會影響 landmarks；目前以單手與 Windows 展示為主，未來可加入校正、資料庫與跨平台支援。",
        "",
    ]
    SCRIPT_PATH.write_text("\n".join(lines), encoding="utf-8")


def build():
    data = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    slides = []
    slides.append(title_slide(data))
    for idx, slide in enumerate(data["slides"][1:], 2):
        if slide.get("diagram"):
            slides.append(diagram_slide(slide, idx, len(data["slides"]) + len(data["code_sections"])))
        else:
            slides.append(standard_slide(slide, idx, len(data["slides"]) + len(data["code_sections"])))

    total = len(data["slides"]) + len(data["code_sections"])
    idx = len(data["slides"]) + 1
    for section in data["code_sections"]:
        slides.append(appendix_slide(section["name"], "程式碼分區註解文字稿", section["points"], idx, total))
        idx += 1

    with zipfile.ZipFile(PPTX_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(len(slides), 1))
        z.writestr("_rels/.rels", rels_root())
        z.writestr("ppt/presentation.xml", presentation_xml(len(slides)))
        z.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(len(slides)))
        z.writestr("ppt/slideMasters/slideMaster1.xml", master_xml())
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>""")
        z.writestr("ppt/slideLayouts/slideLayout1.xml", layout_xml())
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>""")
        z.writestr("ppt/theme/theme1.xml", theme_xml())
        core, app = static_props(len(slides))
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        z.write(COVER_IMAGE, "ppt/media/gesture_cover.png")
        for i, (xml, has_cover) in enumerate(slides, 1):
            z.writestr(f"ppt/slides/slide{i}.xml", xml)
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", slide_rels(has_cover))

    write_notes(data)
    print(PPTX_PATH)
    print(SCRIPT_PATH)
    print(f"slides={len(slides)}")


if __name__ == "__main__":
    build()
