"""Birthday wishlist — small Flask app with persistent item reservations."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, g, jsonify, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "wishlist.db"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "public" / "static"),
)
app.config.update(
    DATABASE=DATABASE,
    ADMIN_KEY=os.environ.get("BIRTHDAY_ADMIN_KEY", "260920091"),
)


# Items imported from Masha's Gold Apple shared cart on 10 September 2026.
# Prices are promotional and can change in the shop before the birthday.
INITIAL_WISHES = [
    {
        "title": "Зубная щётка жёсткая",
        "brand": "R.O.C.S. Smart",
        "category": "other",
        "price": 317,
        "link": "https://goldapple.ru/13580400006-model-naja",
        "image": "https://cdn-01.goldapple.ru/p/p/13580400006/web/696d674d61696e8ddc3deb3ab20a0.jpg",
        "emoji": "🪥",
        "priority": "Буду рада",
        "note": "1 шт. · в ассортименте",
    },
    {
        "title": "Крем для лица с календулой",
        "brand": "WELEDA Calendula Facial Care for Children",
        "category": "beauty",
        "price": 1089,
        "link": "https://goldapple.ru/15181100004-calendula-facial-care-for-children",
        "image": "https://cdn-01.goldapple.ru/p/p/15181100004/web/696d674d61696e5f37383664626365393837343434396230383939373934393530373731613835618def13eebca12ef.jpg",
        "emoji": "🌼",
        "priority": "Буду рада",
        "note": "50 мл",
    },
    {
        "title": "Анти-акне сыворотка с цинком и ниацинамидом",
        "brand": "ART & FACT Niacinamide 10% + Zinc 1%",
        "category": "beauty",
        "price": 340,
        "link": "https://goldapple.ru/19000039298-niacinamide-10-zinc-1-sebum-regulating-anti-acne",
        "image": "https://cdn-01.goldapple.ru/p/p/19000039298/web/696d674d61696e5f63363731633130353135623434373765626463633933396463646634613332318deee2e11d88311.jpg",
        "emoji": "🫧",
        "priority": "Буду рада",
        "note": "30 мл",
    },
    {
        "title": "Парфюмированный гель для душа",
        "brand": "JMELLA In France Femme Fatale Body Wash",
        "category": "beauty",
        "price": 522,
        "link": "https://goldapple.ru/19000080182-in-france-femme-fatale-body-wash",
        "image": "https://cdn-01.goldapple.ru/p/p/19000080182/web/696d674d61696e8ddc4f26199bc0c.jpg",
        "emoji": "🌹",
        "priority": "Буду рада",
        "note": "500 мл",
    },
    {
        "title": "Увлажняющий лосьон для лица",
        "brand": "CLINIQUE Dramatically Different Moisturizing +",
        "category": "beauty",
        "price": 480,
        "link": "https://goldapple.ru/19000219985-dramatically-different-moisturizing-lotion",
        "image": "https://cdn-01.goldapple.ru/p/p/19000219985/web/696d674d61696e5f34366463613531313565646434663432623564323664376566626139633465398de60064e9de65d.jpg",
        "emoji": "💧",
        "priority": "Буду рада",
        "note": "15 мл",
    },
    {
        "title": "Салициловый лосьон для лица",
        "brand": "STOPPROBLEM Ultra Control",
        "category": "beauty",
        "price": 370,
        "link": "https://goldapple.ru/19000335089-ultra-control-ot-prysej-i-cernyh-tocek",
        "image": "https://ccdn.goldapple.ru/p/p/19000335089/web/696d674d61696e8ddc5a37db2c1ff.jpg",
        "emoji": "✨",
        "priority": "Буду рада",
        "note": "200 мл · от прыщей и чёрных точек",
    },
    {
        "title": "Гель для укладки кудрявых волос",
        "brand": "КУДРЯВЫЙ МЕТОД №4 Sakura",
        "category": "hair",
        "price": 746,
        "link": "https://goldapple.ru/19000409147-sakura",
        "image": "https://ccdn.goldapple.ru/p/p/19000409147/web/696d674d61696e5f62623861653862383461643734653032396663383434383462303337383262338decc5fb1f1fb49.jpg",
        "emoji": "〰️",
        "priority": "Буду рада",
        "note": "300 мл",
    },
    {
        "title": "Маска для вьющихся волос",
        "brand": "LEVRANA Pro Bio Hair Fatal Curls",
        "category": "hair",
        "price": 519,
        "link": "https://goldapple.ru/19000436993-pro-bio-hair-fatal-curls",
        "image": "https://ccdn.goldapple.ru/p/p/19000436993/web/696d674d61696e5f38383239363232316162373134343434613639306632616336366230323031378dde08d5447702e.jpg",
        "emoji": "🫶",
        "priority": "Буду рада",
        "note": "250 мл",
    },
    {
        "title": "Тушь для ресниц",
        "brand": "B.COLOUR PROFESSIONAL Capsule Peptide Thermo",
        "category": "makeup",
        "price": 647,
        "link": "https://goldapple.ru/19000455194-capsule-peptide-thermo",
        "image": "https://ccdn.goldapple.ru/p/p/19000455194/web/696d674d61696e5f35626138353564663635363534633533613230383866356633653939613161318ddef9f8a106a55.jpg",
        "emoji": "🖤",
        "priority": "Буду рада",
        "note": "7,3 мл · оттенок 10 Ultra Black",
    },
    {
        "title": "Кондиционер для кудрявых волос",
        "brand": "ГЕЛЬТЕК Curly",
        "category": "hair",
        "price": 177,
        "link": "https://goldapple.ru/19000455907-curly",
        "image": "https://pcdn.goldapple.ru/p/p/19000455907/web/696d674d61696e5f66643438616239626138343334626566626139393562333930363734626166668ddef9713775fea.jpg",
        "emoji": "〰️",
        "priority": "Буду рада",
        "note": "30 мл",
    },
    {
        "title": "Тушь с эффектом сценического объёма",
        "brand": "VIVIENNE SABO Cabaret",
        "category": "makeup",
        "price": 339,
        "link": "https://goldapple.ru/3205400004-cabaret",
        "image": "https://pcdn.goldapple.ru/p/p/3205400004/web/696d674d61696e8ddc3cb9138d1c7.jpg",
        "emoji": "🖤",
        "priority": "Буду рада",
        "note": "9 мл · оттенок 01 чёрный",
    },
    {
        "title": "Гель для бровей и ресниц",
        "brand": "ART-VISAGE Fix&Care",
        "category": "makeup",
        "price": 229,
        "link": "https://goldapple.ru/3762800002-superfiksacija",
        "image": "https://pcdn.goldapple.ru/p/p/3762800002/web/696d674d61696e8ddc3e0dbd394bf.jpg",
        "emoji": "✨",
        "priority": "Буду рада",
        "note": "4 мл · прозрачный",
    },
    {
        "title": "Салициловая суспензия для локального нанесения",
        "brand": "ПРОПЕЛЛЕР Boltushka",
        "category": "beauty",
        "price": 232,
        "link": "https://goldapple.ru/6990100052-boltushka",
        "image": "https://cdn-01.goldapple.ru/p/p/6990100052/web/696d674d61696e8ddc3b1131e58fd.jpg",
        "emoji": "🌟",
        "priority": "Буду рада",
        "note": "25 мл",
    },
    {
        "title": "Бронзер с эффектом сияния",
        "brand": "CATRICE Sun Lover Glow",
        "category": "makeup",
        "price": 553,
        "link": "https://goldapple.ru/69987500001-sun-lover-glow-bronzing-powder",
        "image": "https://cdn-01.goldapple.ru/p/p/69987500001/web/696d674d61696e5f30353934646138653631366534326134383937656232646238323231373364628dec2d633fc2332.jpg",
        "emoji": "☀️",
        "priority": "Буду рада",
        "note": "8 г · оттенок 010",
    },
    {
        "title": "Зубная паста",
        "brand": "BIOREPAIR Pro White",
        "category": "other",
        "price": 735,
        "link": "https://goldapple.ru/90060100004-pro-white",
        "image": "https://cdn-01.goldapple.ru/p/p/90060100004/web/696d674d61696e5f63313737656162346531303234653339386461376631663062636533323439308de9492ebaccb6c.jpg",
        "emoji": "🪥",
        "priority": "Буду рада",
        "note": "75 мл",
    },
    {
        "title": "Патчи для лица от акне",
        "brand": "YOOAH Stars for Spots",
        "category": "beauty",
        "price": 389,
        "link": "https://goldapple.ru/99000154738-yooah-stars-for-spots-hydrocolloid-acne-patches",
        "image": "https://ccdn.goldapple.ru/p/p/99000154738/web/696d674d61696e5f63633038323730626633376134636533386238653839623965306361376265628dec170ec6c89a1.jpg",
        "emoji": "⭐",
        "priority": "Буду рада",
        "note": "51 шт.",
    },
    {
        "title": "Пудра для лица",
        "brand": "HOLIKA HOLIKA Puri Pore No Sebum Powder",
        "category": "makeup",
        "price": 754,
        "link": "https://goldapple.ru/99493100002-puri-pore-no-sebum",
        "image": "https://pcdn.goldapple.ru/p/p/99493100002/web/696d674d61696e8ddc43e1702c97a.jpg",
        "emoji": "🌸",
        "priority": "Буду рада",
        "note": "7 г",
    },
]

PLACEHOLDER_TITLES = {
    "Парфюм мечты",
    "Средство для ухода",
    "Что-то уютное",
    "Маленькая радость",
}


def get_db() -> sqlite3.Connection:
    """Open one database connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: object | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Create tables and only seed sample cards on first launch."""
    with closing(sqlite3.connect(app.config["DATABASE"])) as db:
        db.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS wishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                brand TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                price INTEGER NOT NULL CHECK(price >= 0),
                link TEXT NOT NULL DEFAULT '',
                image TEXT NOT NULL DEFAULT '',
                emoji TEXT NOT NULL DEFAULT '🎁',
                priority TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'available'
                    CHECK(status IN ('available', 'reserved')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wish_id INTEGER NOT NULL UNIQUE,
                guest_name TEXT NOT NULL,
                contact TEXT NOT NULL DEFAULT '',
                message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(wish_id) REFERENCES wishes(id) ON DELETE CASCADE
            );
            """
        )
        existing_titles = {row[0] for row in db.execute("SELECT title FROM wishes")}
        reservation_count = db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
        # Upgrade the unedited four-card demo that was created before the real
        # Gold Apple cart arrived. Never overwrite a list that has reservations.
        should_seed = not existing_titles or (
            existing_titles == PLACEHOLDER_TITLES and reservation_count == 0
        )
        if should_seed:
            if existing_titles:
                db.execute("DELETE FROM wishes")
            db.executemany(
                """
                INSERT INTO wishes
                    (title, brand, category, price, link, image, emoji, priority, note)
                VALUES
                    (:title, :brand, :category, :price, :link, :image, :emoji, :priority, :note)
                """,
                INITIAL_WISHES,
            )
        db.commit()


@app.template_filter("rubles")
def rubles(value: int) -> str:
    return f"{int(value):,}".replace(",", " ") + " ₽"


def all_wishes(include_reserved: bool = True) -> list[dict]:
    query = "SELECT * FROM wishes"
    if not include_reserved:
        query += " WHERE status = 'available'"
    query += " ORDER BY price ASC, id ASC"
    return [dict(row) for row in get_db().execute(query).fetchall()]


@app.get("/")
def home():
    wishes = all_wishes()
    available = sum(wish["status"] == "available" for wish in wishes)
    return render_template("index.html", preview=wishes[:3], total=len(wishes), available=available)


@app.get("/wishlist")
def wishlist():
    return render_template("wishlist.html", wishes=all_wishes())


@app.get("/thanks")
def thanks():
    return render_template("thanks.html")


@app.get("/api/wishes")
def wishes_api():
    return jsonify(all_wishes())


@app.post("/api/wishes/<int:wish_id>/reserve")
def reserve_wish(wish_id: int):
    """Reserve one gift. The conditional update prevents double booking."""
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()

    if not message:
        return jsonify(error="Оставь, пожалуйста, пожелание для Маши."), 400
    if len(message) > 500:
        return jsonify(error="Слишком длинное сообщение — попробуй короче."), 400

    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        updated = db.execute(
            "UPDATE wishes SET status = 'reserved' WHERE id = ? AND status = 'available'", (wish_id,)
        ).rowcount
        if updated != 1:
            db.rollback()
            return jsonify(error="Этот подарок уже забронировали. Выбери другой — там тоже много красоты!"), 409
        db.execute(
            "INSERT INTO reservations (wish_id, guest_name, contact, message) VALUES (?, ?, ?, ?)",
            (wish_id, "", "", message),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify(error="Этот подарок уже забронировали."), 409

    return jsonify(ok=True, redirect=url_for("thanks"))


def check_admin_key() -> None:
    supplied = request.headers.get("X-Admin-Key", "")
    if supplied != app.config["ADMIN_KEY"]:
        abort(401)


@app.get("/api/admin/reservations")
def reservations_api():
    check_admin_key()
    rows = get_db().execute(
        """
        SELECT reservations.id, message, reservations.created_at,
               wishes.title AS wish_title, wishes.price AS wish_price
        FROM reservations JOIN wishes ON wishes.id = reservations.wish_id
        ORDER BY reservations.created_at DESC
        """
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/admin/reservations/<int:reservation_id>/cancel")
def cancel_reservation(reservation_id: int):
    check_admin_key()
    db = get_db()
    reservation = db.execute("SELECT wish_id FROM reservations WHERE id = ?", (reservation_id,)).fetchone()
    if reservation is None:
        return jsonify(error="Бронь не найдена."), 404
    db.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    db.execute("UPDATE wishes SET status = 'available' WHERE id = ?", (reservation["wish_id"],))
    db.commit()
    return jsonify(ok=True)


@app.route("/masha-admin", methods=["GET", "POST"])
def admin():
    error = None
    key = ""
    rows: list[dict] | None = None
    if request.method == "POST":
        key = request.form.get("key", "")
        if key != app.config["ADMIN_KEY"]:
            error = "Неверный ключ. Его нужно задать в переменной BIRTHDAY_ADMIN_KEY."
        else:
            rows = [
                dict(row)
                for row in get_db().execute(
                    """
                    SELECT reservations.id, message, reservations.created_at,
                           wishes.title AS wish_title, wishes.price AS wish_price
                    FROM reservations JOIN wishes ON wishes.id = reservations.wish_id
                    ORDER BY reservations.created_at DESC
                    """
                ).fetchall()
            ]
    return render_template("admin.html", rows=rows, error=error, key=key if rows is not None else "")


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5050, debug=os.environ.get("FLASK_DEBUG") == "1")
