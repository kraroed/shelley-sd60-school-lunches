/* Shelley SD60 Lunch Card
 * Custom Lovelace card for the linq_shelley Home Assistant integration.
 * No external libraries required.
 */
const SCHOOLS = [
  { key: "dean_goodsell", name: "Dean Goodsell Elementary", prefix: "dean_goodsell_elementary" },
  { key: "hobbs_middle", name: "Hobbs Middle School", prefix: "hobbs_middle_school" },
  { key: "riverview", name: "Riverview Elementary", prefix: "riverview_elementary" },
  { key: "shelley_high", name: "Shelley High School", prefix: "shelley_high_school" },
  { key: "stuart", name: "Stuart Elementary", prefix: "stuart_elementary" },
  { key: "sunrise", name: "Sunrise Elementary", prefix: "sunrise_elementary" },
];

const GROUPS = {
  hobbs_middle: [
    { label: "Main Menu", entity: "sensor.hobbs_middle_school_lunch_main_menu", icon: "🍽️" },
    { label: "Second Line", entity: "sensor.hobbs_middle_school_lunch_second_line", icon: "🍕" },
    { label: "Shared Items", entity: "sensor.hobbs_middle_school_lunch_shared_items", icon: "🥗" },
  ],
  shelley_high: [
    { label: "Main Menu", entity: "sensor.shelley_high_school_lunch_main_menu", icon: "🍽️" },
    { label: "Hot n Ready", entity: "sensor.shelley_high_school_lunch_hot_n_ready", icon: "🔥" },
    { label: "Grab N Go", entity: "sensor.shelley_high_school_lunch_grab_n_go", icon: "🥪" },
    { label: "Shared Items", entity: "sensor.shelley_high_school_lunch_shared_items", icon: "🥗" },
  ],
};

const h = (tag, attrs = {}, children = []) => {
  const el = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === "class") el.className = v;
    else if (k === "text") el.textContent = v;
    else if (k === "style") el.setAttribute("style", v);
    else el.setAttribute(k, v);
  });
  children.forEach(child => el.append(child));
  return el;
};

class ShelleySD60LunchCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._school = "hobbs_middle";
    this._period = "today";
  }

  setConfig(config) {
    if (!config || typeof config !== "object") throw new Error("Please provide a valid Shelley SD60 Lunch Card configuration.");
    this._config = config;
    if (config.default_school && SCHOOLS.some(s => s.key === config.default_school)) this._school = config.default_school;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() { return this._period === "14days" ? 8 : 5; }

  static getStubConfig() {
    return { type: "custom:shelley-sd60-lunch-card", title: "Shelley SD60 Lunch Menu", default_school: "hobbs_middle" };
  }

  _entity(key, period) {
    const school = SCHOOLS.find(s => s.key === key) || SCHOOLS[0];
    const defaults = {
      today: `sensor.${school.prefix}_lunch_today`,
      tomorrow: `sensor.${school.prefix}_lunch_tomorrow`,
      "14days": `sensor.${school.prefix}_lunch_14_day_menu`,
    };
    const configured = this._config?.entities?.[key]?.[period];
    return configured || defaults[period];
  }

  _state(entityId) { return this._hass?.states?.[entityId] || null; }

  _dateLabel(dateString) {
    if (!dateString) return "";
    const d = new Date(dateString + "T12:00:00");
    return Number.isNaN(d.getTime()) ? dateString : d.toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" });
  }

  _items(value) {
    if (Array.isArray(value)) return value.map(v => typeof v === "string" ? v : v?.name || v?.title || JSON.stringify(v)).filter(Boolean);
    if (typeof value === "string" && value.trim()) return value.split(/\s*,\s*/).filter(Boolean);
    return [];
  }

  _menuFor(state, period) {
    if (!state) return { status: "missing", items: [], date: "" };
    const attrs = state.attributes || {};
    if (period === "14days") {
      const menu = attrs.menu && typeof attrs.menu === "object" ? attrs.menu : {};
      return { status: "ok", days: Object.entries(menu).sort(([a], [b]) => a.localeCompare(b)).map(([date, items]) => ({ date, items: this._items(items) })), date: "" };
    }
    return { status: state.state === "unavailable" || state.state === "unknown" ? state.state : "ok", items: this._items(attrs.menu), date: attrs.date || "" };
  }

  _render() {
    if (!this.shadowRoot || !this._config) return;
    const school = SCHOOLS.find(s => s.key === this._school) || SCHOOLS[0];
    const title = this._config.title || "Shelley SD60 Lunch Menu";
    const style = h("style", { text: `
      :host{display:block;color:var(--primary-text-color);font-family:var(--paper-font-body1_-_font-family,Roboto,Noto,sans-serif)}
      ha-card{overflow:hidden;background:var(--ha-card-background,var(--card-background-color));border-radius:var(--ha-card-border-radius,12px);border:1px solid var(--divider-color);box-shadow:var(--ha-card-box-shadow,none)}
      .hero{padding:18px 18px 14px;background:linear-gradient(125deg,var(--primary-color),var(--accent-color,var(--primary-color)));color:var(--text-primary-color,#fff)}
      .hero-top{display:flex;align-items:center;gap:12px}.apple{font-size:32px}.title{font-size:20px;font-weight:700;line-height:1.25}.subtitle{opacity:.88;font-size:13px;margin-top:4px}
      .controls{padding:14px 16px 0;display:grid;gap:12px}.select{width:100%;box-sizing:border-box;background:var(--card-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);border-radius:10px;padding:11px;font:inherit}
      .tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.tab{border:1px solid var(--divider-color);border-radius:9px;background:var(--secondary-background-color);color:var(--primary-text-color);padding:10px 4px;font:inherit;font-size:13px;cursor:pointer}.tab[aria-pressed=true]{background:var(--primary-color);border-color:var(--primary-color);color:var(--text-primary-color,#fff);font-weight:600}
      .body{padding:14px 16px 18px}.date{font-size:14px;font-weight:600;margin:0 0 12px;color:var(--secondary-text-color)}.section{border:1px solid var(--divider-color);border-radius:12px;padding:13px;margin-bottom:10px}.section-head{display:flex;align-items:center;gap:9px;font-weight:700;margin-bottom:8px}.section-icon{font-size:22px}.items{margin:0;padding-left:22px;line-height:1.55}.items li{padding:2px 0}.empty{background:var(--secondary-background-color);border-radius:10px;padding:14px;color:var(--secondary-text-color);line-height:1.45}.empty strong{display:block;color:var(--primary-text-color);margin-bottom:4px}.day{margin:12px 0 16px}.day-title{font-weight:700;margin-bottom:8px}.footer{border-top:1px solid var(--divider-color);padding:10px 16px;color:var(--secondary-text-color);font-size:11px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
    `});
    const card = h("ha-card");
    const hero = h("div", { class: "hero" }, [
      h("div", { class: "hero-top" }, [
        h("span", { class: "apple", text: "🍎" }),
        h("div", {}, [h("div", { class: "title", text: title }), h("div", { class: "subtitle", text: "Shelley School District 60 · School meals" })])
      ])
    ]);
    const select = h("select", { class: "select", "aria-label": "Select school" });
    SCHOOLS.forEach(s => {
      const option = h("option", { value: s.key, text: s.name });
      if (s.key === this._school) option.selected = true;
      select.append(option);
    });
    select.addEventListener("change", ev => { this._school = ev.target.value; this._render(); });
    const tabs = h("div", { class: "tabs" });
    [["today","Today"],["tomorrow","Tomorrow"],["14days","14 Days"]].forEach(([key,label]) => {
      const b = h("button", { class: "tab", type: "button", text: label, "aria-pressed": String(this._period === key) });
      b.addEventListener("click", () => { this._period = key; this._render(); });
      tabs.append(b);
    });
    const controls = h("div", { class: "controls" }, [select, tabs]);
    const body = h("div", { class: "body" });
    const dateEntity = this._state(this._entity(this._school, this._period));
    const menu = this._menuFor(dateEntity, this._period);

    if (this._period === "14days") {
      if (!dateEntity) {
        body.append(this._empty("Menu sensor not found", `Could not find ${this._entity(this._school, this._period)}. You can override entity IDs in the card configuration.`));
      } else if (!menu.days?.length) {
        body.append(this._empty("No upcoming menu data", "The integration has not provided any menu days yet."));
      } else {
        menu.days.forEach(day => {
          const section = h("div", { class: "day" }, [h("div", { class: "day-title", text: this._dateLabel(day.date) || day.date })]);
          section.append(this._itemsSection("Lunch menu", "🍽️", day.items));
          body.append(section);
        });
      }
    } else if (GROUPS[this._school]) {
      const schoolGroups = GROUPS[this._school];
      let foundGroup = false;
      schoolGroups.forEach(group => {
        const entityId = this._config?.entities?.[this._school]?.groups?.[group.label] || group.entity;
        const groupState = this._state(entityId);
        if (!groupState) {
          body.append(this._empty(group.label, `Sensor not found: ${entityId}`));
          return;
        }
        foundGroup = true;
        const groupMenu = groupState.attributes?.menu;
        const menuDate = dateEntity?.attributes?.date;
        const groupValue = groupMenu && !Array.isArray(groupMenu) && typeof groupMenu === "object"
          ? (groupMenu[menuDate] || [])
          : groupMenu;
        const groupItems = this._items(groupValue);
        body.append(this._itemsSection(group.label, group.icon, groupItems, groupState.state));
      });
      if (!foundGroup) body.append(this._empty("Menu unavailable", "No menu-group sensors were found."));
      if (dateEntity?.attributes?.date) body.prepend(h("div", { class: "date", text: this._dateLabel(dateEntity.attributes.date) }));
    } else {
      if (!dateEntity) {
        body.append(this._empty("Menu sensor not found", `Could not find ${this._entity(this._school, this._period)}. Check the entity ID or override it in the card configuration.`));
      } else {
        if (menu.date) body.append(h("div", { class: "date", text: this._dateLabel(menu.date) }));
        if (menu.status === "unavailable" || menu.status === "unknown") {
          body.append(this._empty("Menu sensor " + menu.status, "Home Assistant does not currently have a menu value for this sensor."));
        } else {
          body.append(this._itemsSection("Lunch menu", "🍽️", menu.items, dateEntity.state));
        }
      }
    }

    const footer = h("div", { class: "footer" }, [
      h("span", { text: "Source: LINQ Connect menu integration" }),
      h("span", { text: dateEntity?.last_updated ? "Updated " + new Date(dateEntity.last_updated).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "Waiting for sensor data" })
    ]);
    card.append(hero, controls, body, footer);
    this.shadowRoot.replaceChildren(style, card);
  }

  _itemsSection(label, icon, items, state) {
    const section = h("section", { class: "section" }, [
      h("div", { class: "section-head" }, [h("span", { class: "section-icon", text: icon }), h("span", { text: label })])
    ]);
    if (items?.length) {
      const list = h("ul", { class: "items" });
      items.forEach(item => list.append(h("li", { text: item })));
      section.append(list);
    } else {
      section.append(h("div", { class: "empty", text: state === "unavailable" ? "Menu data is unavailable right now." : "No menu items reported for this section." }));
    }
    return section;
  }

  _empty(title, message) {
    return h("div", { class: "empty" }, [h("strong", { text: title }), h("span", { text: message })]);
  }
}

if (!customElements.get("shelley-sd60-lunch-card")) {
  customElements.define("shelley-sd60-lunch-card", ShelleySD60LunchCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "shelley-sd60-lunch-card",
    name: "Shelley SD60 Lunch Menu",
    description: "Visual lunch menu card for Shelley School District 60 using the linq_shelley integration.",
    preview: true
  });
}
