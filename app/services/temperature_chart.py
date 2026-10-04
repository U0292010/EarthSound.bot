from collections.abc import Sequence
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


def build_temperature_chart(
    location_name: str,
    yearly_values: Sequence[tuple[int, float]],
) -> bytes:
    return build_yearly_line_chart(
        "Temperature",
        location_name,
        yearly_values,
        "°C",
        "ANNUAL MEAN / ILLUSTRATIVE TEST DATA",
    )


def build_yearly_line_chart(
    metric_name: str,
    location_name: str,
    yearly_values: Sequence[tuple[int, float]],
    unit_label: str,
    subtitle: str,
    value_decimals: int = 1,
) -> bytes:
    if not yearly_values:
        raise ValueError("At least one yearly data value is required.")

    width, height = 1000, 620
    left, right, top, bottom = 110, 55, 115, 100
    plot_width = width - left - right
    plot_height = height - top - bottom
    image = Image.new("RGB", (width, height), "#f7f8f5")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default(size=34)
    label_font = ImageFont.load_default(size=20)
    small_font = ImageFont.load_default(size=17)

    draw.text((left, 35), f"{metric_name} | {location_name}", font=title_font, fill="#173b3a")
    draw.text(
        (left, 78),
        f"{subtitle}  /  {unit_label}",
        font=small_font,
        fill="#60716d",
    )

    values = [value for _, value in yearly_values]
    minimum = min(values)
    maximum = max(values)
    padding = max(0.3, (maximum - minimum) * 0.2)
    lower_bound = minimum - padding
    upper_bound = maximum + padding

    for tick_index in range(5):
        ratio = tick_index / 4
        y = top + round(plot_height * ratio)
        value = upper_bound - (upper_bound - lower_bound) * ratio
        formatted_value = (
            f"{value:,.0f}" if value_decimals == 0 else f"{value:.{value_decimals}f}"
        )
        draw.line((left, y, left + plot_width, y), fill="#dce4df", width=2)
        draw.text(
            (left - 12, y),
            f"{formatted_value} {unit_label}",
            font=small_font,
            fill="#52635f",
            anchor="rm",
        )

    points = []
    last_index = len(yearly_values) - 1
    for index, (year, value) in enumerate(yearly_values):
        x = left + (round(plot_width * index / last_index) if last_index else plot_width // 2)
        y = top + round(plot_height * (upper_bound - value) / (upper_bound - lower_bound))
        points.append((x, y))
        draw.text((x, top + plot_height + 25), str(year), font=label_font, fill="#30423f", anchor="mt")

    if len(points) > 1:
        draw.line(points, fill="#17816d", width=6, joint="curve")

    for (x, y), (_, value) in zip(points, yearly_values):
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill="#e7784b", outline="#f7f8f5", width=3)
        point_label = f"{value:,.0f}" if value_decimals == 0 else f"{value:.{value_decimals}f}"
        draw.text((x, y - 20), point_label, font=small_font, fill="#173b3a", anchor="ms")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()