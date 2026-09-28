const MODEL_NAME = "hangarCarouselPlus";
const CARD_PREFIX = "vehicleCard-";

const LABELS = {
  en: {
    all: "All vehicles",
    all_description: "Clears every HCP filter. The standard client filters remain active.",
    field_mod_incomplete: "Field Modification incomplete",
    field_mod_incomplete_description: "Vehicles eligible for Field Modification whose progression is not fully completed.",
    crew_not_maxed: "Crew training incomplete",
    crew_not_maxed_description: "Vehicles with missing crew, incomplete qualification or efficiency, unfinished perks, or a perk available to learn.",
    non_elite: "Research incomplete",
    non_elite_description: "Non-elite vehicles with modules or following vehicles left to research.",
    premium: "Premium vehicles",
    premium_description: "Owned Premium vehicles in your Garage.",
    reward_special: "Reward / special vehicles",
    reward_special_description: "Owned reward and special vehicles. Premium vehicles already have a standard client filter.",
    not_ready: "Not ready for battle",
    not_ready_description: "Vehicles needing repairs, with an incomplete crew, or with too little ammunition.",
    no_mastery: "Without Ace Tanker",
    no_mastery_description: "Vehicles that have not yet earned the Ace Tanker mastery badge.",
    marks_incomplete: "Fewer than three Marks",
    marks_incomplete_description: "Vehicles with zero, one, or two Marks of Excellence.",
    research_ready: "Research available",
    research_ready_description: "Vehicles with enough vehicle XP to unlock at least one immediately available module or following vehicle.",
    sort_default: "Default order",
    sort_battles: "Battles",
    sort_winRate: "Win rate",
    sort_averageDamage: "Average damage",
    sort_marksOnGun: "Marks of Excellence",
    sort_battlePassPoints: "Battle Pass points earned",
    sort_lastPlayed: "Last played (HCP)",
    sort_priority: "Primary > Field Modification > default",
    sort_random: "Random order",
    sort_random_description: "Click to shuffle the tanks. Click again for a new order.",
    smart_filters: "HCP smart filters",
    sorting: "HCP sorting",
    toggle_on: "ON",
    toggle_off: "OFF",
    matches: "Matching vehicles",
    stat_battles: "B",
    stat_win_rate: "WR",
    stat_damage: "D",
    stat_marks: "MoE",
    carousel_rows: "Carousel rows",
    carousel_rows_description: "Number of vehicle rows displayed in the hangar carousel.",
    carousel_auto: "Automatic rows",
    carousel_auto_description: "Uses 1 row for up to 8 matching vehicles, 2 for up to 16, 3 for up to 24, and 4 above 24.",
    ascending: "Ascending",
    descending: "Descending",
    refresh: "Refresh HCP data",
    refresh_description: "Recalculate smart-filter counts and carousel statistics.",
    unavailable: "Vehicle playlists are unavailable in this client mode"
  },
  ru: {
    all: "Вся техника",
    all_description: "Сбрасывает все фильтры HCP. Стандартные фильтры клиента остаются активными.",
    field_mod_incomplete: "Полевая модернизация не завершена",
    field_mod_incomplete_description: "Техника с доступной полевой модернизацией, у которой открыты не все уровни.",
    crew_not_maxed: "Экипаж не прокачан",
    crew_not_maxed_description: "Техника с неполным экипажем, незавершённой квалификацией, эффективностью или навыками, либо доступным навыком для изучения.",
    non_elite: "Исследование не завершено",
    non_elite_description: "Неэлитная техника, у которой остались неисследованные модули или следующая техника.",
    premium: "Премиум техника",
    premium_description: "Премиум техника в вашем Ангаре.",
    reward_special: "Наградная / акционная техника",
    reward_special_description: "Наградная и акционная техника в Ангаре. Для премиум техники в клиенте уже есть стандартный фильтр.",
    not_ready: "Не готова к бою",
    not_ready_description: "Техника, требующая ремонта, с неполным экипажем или недостаточным боекомплектом.",
    no_mastery: "Без «Мастера»",
    no_mastery_description: "Техника, на которой ещё не получен знак классности «Мастер».",
    marks_incomplete: "Меньше трёх отметок",
    marks_incomplete_description: "Техника без отметок или с одной либо двумя отметками на орудии.",
    research_ready: "Доступно исследование",
    research_ready_description: "Техника, у которой хватает опыта для исследования доступного модуля или следующей машины.",
    sort_default: "Обычный порядок",
    sort_battles: "Бои",
    sort_winRate: "Победы",
    sort_averageDamage: "Средний урон",
    sort_marksOnGun: "Отметки",
    sort_battlePassPoints: "Очки Боевого пропуска",
    sort_lastPlayed: "Последний бой (HCP)",
    sort_priority: "Основные > полевая модернизация > обычный порядок",
    sort_random: "Случайный порядок",
    sort_random_description: "Нажмите, чтобы перемешать танки. Нажмите ещё раз для нового порядка.",
    smart_filters: "Умные фильтры HCP",
    sorting: "Сортировка HCP",
    toggle_on: "ВКЛ",
    toggle_off: "ВЫКЛ",
    matches: "Подходящая техника",
    stat_battles: "Б",
    stat_win_rate: "П",
    stat_damage: "У",
    stat_marks: "Отм.",
    carousel_rows: "Ряды карусели",
    carousel_rows_description: "Количество рядов техники в карусели Ангара.",
    carousel_auto: "Автоматические ряды",
    carousel_auto_description: "1 ряд для 1–8 машин, 2 для 9–16, 3 для 17–24 и 4 для большего количества.",
    ascending: "По возрастанию",
    descending: "По убыванию",
    refresh: "Обновить данные HCP",
    refresh_description: "Пересчитать фильтры и статистику в карусели.",
    unavailable: "Плейлисты техники недоступны в этом режиме"
  },
  uk: {
    all: "Уся техніка",
    all_description: "Скидає всі фільтри HCP. Стандартні фільтри клієнта залишаються активними.",
    field_mod_incomplete: "Польову модернізацію не завершено",
    field_mod_incomplete_description: "Техніка з доступною польовою модернізацією, для якої відкрито не всі рівні.",
    crew_not_maxed: "Екіпаж не прокачаний",
    crew_not_maxed_description: "Техніка з неповним екіпажем, незавершеною кваліфікацією, ефективністю чи навичками або доступною навичкою для вивчення.",
    non_elite: "Дослідження не завершено",
    non_elite_description: "Неелітна техніка, для якої залишилися недосліджені модулі або наступна техніка.",
    premium: "Преміум техніка",
    premium_description: "Преміум техніка у вашому Ангарі.",
    reward_special: "Нагородна / акційна техніка",
    reward_special_description: "Нагородна й акційна техніка в Ангарі. Для преміум техніки в клієнті вже є стандартний фільтр.",
    not_ready: "Не готова до бою",
    not_ready_description: "Техніка, що потребує ремонту, має неповний екіпаж або недостатній боєкомплект.",
    no_mastery: "Без «Майстра»",
    no_mastery_description: "Техніка, на якій ще не здобуто знак класності «Майстер».",
    marks_incomplete: "Менше трьох відміток",
    marks_incomplete_description: "Техніка без відміток або з однією чи двома відмітками на гарматі.",
    research_ready: "Доступне дослідження",
    research_ready_description: "Техніка, що має достатньо досвіду для дослідження доступного модуля або наступної машини.",
    sort_default: "Звичайний порядок",
    sort_battles: "Бої",
    sort_winRate: "Перемоги",
    sort_averageDamage: "Середня шкода",
    sort_marksOnGun: "Відмітки",
    sort_battlePassPoints: "Очки Бойової перепустки",
    sort_lastPlayed: "Останній бій (HCP)",
    sort_priority: "Основні > польова модернізація > звичайний порядок",
    sort_random: "Випадковий порядок",
    sort_random_description: "Натисніть, щоб перемішати танки. Натисніть ще раз для нового порядку.",
    smart_filters: "Розумні фільтри HCP",
    sorting: "Сортування HCP",
    toggle_on: "УВІМК",
    toggle_off: "ВИМК",
    matches: "Підхожа техніка",
    stat_battles: "Б",
    stat_win_rate: "П",
    stat_damage: "Ш",
    stat_marks: "Відм.",
    carousel_rows: "Ряди каруселі",
    carousel_rows_description: "Кількість рядів техніки в каруселі Ангара.",
    carousel_auto: "Автоматичні ряди",
    carousel_auto_description: "1 ряд для 1–8 машин, 2 для 9–16, 3 для 17–24 та 4 для більшої кількості.",
    ascending: "За зростанням",
    descending: "За спаданням",
    refresh: "Оновити дані HCP",
    refresh_description: "Перерахувати фільтри та статистику в каруселі.",
    unavailable: "Плейлисти техніки недоступні в цьому режимі"
  }
};

Object.assign(LABELS, window.HCP_I18N || {});

const LANGUAGE_ALIASES = {
  en_gb: "en",
  en_us: "en",
  en_zw: "en",
  es_ar: "es",
  es_mx: "es",
  pt_br: "pt",
  sr_latn: "sr"
};

const FILTER_ICONS = {
  all: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
  field_mod_incomplete: '<svg viewBox="0 0 24 24"><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3"/><path d="M1 14h6M9 8h6M17 16h6"/></svg>',
  crew_not_maxed: '<svg viewBox="0 0 24 24"><circle cx="10" cy="8" r="4"/><path d="M3 21v-2a6 6 0 0 1 12 0v2M18 14v7M15 17l3-3 3 3"/></svg>',
  non_elite: '<svg viewBox="0 0 24 24"><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="12" cy="19" r="2"/><path d="M7 5h10M6.5 6.5l4.3 10.7M17.5 6.5l-4.3 10.7"/></svg>',
  premium: '<svg viewBox="0 0 24 24"><path d="m12 2 3 6 6.5.9-4.7 4.6 1.1 6.5-5.9-3-5.9 3 1.1-6.5-4.7-4.6L9 8z"/></svg>',
  reward_special: '<svg viewBox="0 0 24 24"><path d="M7 3h10v5a5 5 0 0 1-10 0zM9 20h6M12 13v7M7 5H3v2a4 4 0 0 0 5 4M17 5h4v2a4 4 0 0 1-5 4"/></svg>',
  not_ready: '<svg viewBox="0 0 24 24"><path d="M12 3 2.5 20h19zM12 8v6M12 17.5v.5"/></svg>',
  no_mastery: '<svg viewBox="0 0 24 24"><path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9zM4 4l16 16"/></svg>',
  marks_incomplete: '<svg viewBox="0 0 24 24"><path d="M4 18 8 6l4 12 4-12 4 12M3 21h18"/><circle cx="8" cy="4" r="1"/><circle cx="12" cy="4" r="1"/><circle cx="16" cy="4" r="1"/></svg>',
  research_ready: '<svg viewBox="0 0 24 24"><circle cx="5" cy="12" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 12h5M12 12l5-6M12 12l5 6M9 9l3 3-3 3"/></svg>'
};

const SORT_ICONS = {
  random: '<svg class="hcp-native-sort-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h3c5 0 7 12 12 12h3M17 14l4 4-4 4M3 18h3c2 0 4-3 6-6s4-6 6-6h3M17 2l4 4-4 4"/></svg>',
  default: '<svg class="hcp-native-sort-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 4v16M5 7l3-3 3 3M16 20V4M13 17l3 3 3-3"/></svg>',
  battles: '<svg class="hcp-native-sort-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 20h18M4 20v-6h4v6M10 20V9h4v11M16 20V4h4v16"/></svg>',
  winRate: '<svg class="hcp-native-sort-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="m4 18 5-5 4 3 7-9M15 7h5v5"/></svg>',
  averageDamage: '<svg class="hcp-native-sort-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="m13 2-8 12h6l-1 8 9-13h-6z"/></svg>',
  marksOnGun: '<svg class="hcp-native-sort-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/></svg>',
  battlePassPoints: '<svg class="hcp-native-sort-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3h14v12l-7 6-7-6zM12 6l1.4 2.8 3.1.5-2.2 2.1.5 3.1-2.8-1.5-2.8 1.5.5-3.1-2.2-2.1 3.1-.5z"/></svg>',
  lastPlayed: '<svg class="hcp-native-sort-svg" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6l4 2"/></svg>',
  priority: '<svg class="hcp-native-sort-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="m7 3 1.3 2.7 3 .4-2.2 2.1.5 3-2.6-1.4-2.6 1.4.5-3-2.2-2.1 3-.4zM14 6h7M14 11h7M3 16h18M7 13v6M12 13v6"/></svg>'
};

const SORT_DIRECTION_ICONS = {
  descending: '<svg class="hcp-native-sort-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v16M7 15l5 5 5-5"/></svg>',
  ascending: '<svg class="hcp-native-sort-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20V4M7 9l5-5 5 5"/></svg>'
};

let state = { filters: [], stats: {}, statsConfig: {}, sorting: {}, actionCards: {}, carousel: { rows: 2 }, enabled: false };
let activeFilters = [];
let lastStateJson = "";
let lastActiveFiltersJson = "";
let lastStatsDiagnostic = "";
let scheduled = false;
let renderTimer = null;
let tooltipElement = null;

function unwrap(value) {
  if (value && typeof value === "object" && Object.prototype.hasOwnProperty.call(value, "value")) {
    return value.value;
  }
  return value;
}

function language() {
  const raw = String(state.language || document.documentElement.lang || navigator.language || "en")
    .trim()
    .toLowerCase()
    .replace(/-/g, "_");
  const normalized = LANGUAGE_ALIASES[raw] || raw;
  if (LABELS[normalized]) return normalized;
  const base = normalized.split("_")[0];
  return LABELS[base] ? base : "en";
}

function labels() {
  return Object.assign({}, LABELS.en, LABELS[language()] || {});
}

function findModel() {
  if (!window.subViews) return null;
  for (const id of window.subViews.ids()) {
    const candidate = window.subViews.get(id)?.model?.[MODEL_NAME];
    if (candidate) return candidate;
  }
  return null;
}

function callCommand(commandName, payload) {
  const model = findModel();
  if (!model || typeof model[commandName] !== "function") return false;
  try {
    if (payload === undefined) model[commandName]();
    else model[commandName](payload);
    return true;
  } catch (error) {
    console.error(`[HangarCarouselPlus] ${commandName} failed`, error);
    return false;
  }
}

function debugLog(message) {
  if (state.debug && typeof console.debug === "function") {
    console.debug(`[HangarCarouselPlus] ${message}`);
  }
}

function scheduleRender() {
  if (scheduled || renderTimer !== null) return;
  renderTimer = window.setTimeout(() => {
    renderTimer = null;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      applyCarouselRowsClass();
      applyActionCardsVisibility();
      renderNativeFilterPanel();
      renderCardStats();
    });
  }, 40);
}

function mutationAffectsHcp(mutation) {
  const selector = `[data-test-id^="${CARD_PREFIX}"], [class*="FilterPopover_"]`;
  const target = mutation.target?.nodeType === Node.ELEMENT_NODE ? mutation.target : mutation.target?.parentElement;
  if (target?.matches?.(selector) || target?.closest?.(selector)) return true;
  for (const node of [...mutation.addedNodes, ...mutation.removedNodes]) {
    if (node.nodeType !== Node.ELEMENT_NODE) continue;
    if (node.matches?.(selector) || node.querySelector?.(selector)) return true;
  }
  return false;
}

function applyCarouselRowsClass() {
  const rows = Math.max(1, Math.min(4, Number(state.carousel?.rows || 2)));
  for (const root of [document.documentElement, document.body]) {
    if (!root) continue;
    root.classList.remove("hcp-carousel-rows-1", "hcp-carousel-rows-2", "hcp-carousel-rows-3", "hcp-carousel-rows-4");
    root.classList.add(`hcp-carousel-rows-${rows}`);
  }
}

function applyActionCardsVisibility() {
  const classes = {
    hideBuyTank: "hcp-hide-buy-tank",
    hideBuySlot: "hcp-hide-buy-slot",
    hideRestoreTank: "hcp-hide-restore-tank"
  };
  for (const root of [document.documentElement, document.body]) {
    if (!root) continue;
    for (const [key, className] of Object.entries(classes)) {
      root.classList.toggle(className, Boolean(state.actionCards?.[key]));
    }
  }
}

function formatCompact(value) {
  const number = Number(value || 0);
  if (number >= 10000) return `${(number / 1000).toFixed(number >= 100000 ? 0 : 1)}k`;
  return number.toLocaleString();
}

function masteryLabel(value) {
  return value > 0 ? `M${value}` : "";
}

function winRateBand(value) {
  const winRate = Number(value || 0);
  if (winRate < 47) return "bad";
  if (winRate < 50) return "below-average";
  if (winRate < 52) return "average";
  if (winRate < 55) return "good";
  if (winRate < 60) return "great";
  return "exceptional";
}

function statRows(stats) {
  const fields = state.statsConfig?.fields || [];
  const rows = [];
  if (fields.includes("battles")) {
    rows.push([{ classes: ["battles"], text: `${labels().stat_battles} ${formatCompact(stats.battles)}` }]);
  }
  if (fields.includes("winRate")) {
    const winRate = Number(stats.winRate || 0);
    rows.push([{
      classes: ["win-rate", `win-rate-${winRateBand(winRate)}`],
      text: `${labels().stat_win_rate} ${winRate.toFixed(1)}%`
    }]);
  }
  if (fields.includes("averageDamage")) {
    rows.push([{ classes: ["damage"], text: `${labels().stat_damage} ${formatCompact(stats.averageDamage)}` }]);
  }
  const achievements = [];
  if (fields.includes("mastery") && stats.mastery) {
    achievements.push({ classes: ["mastery", `mastery-${Number(stats.mastery)}`], text: masteryLabel(stats.mastery) });
  }
  if (fields.includes("marksOnGun") && stats.marksOnGun) {
    achievements.push({ classes: ["marks", `marks-${Number(stats.marksOnGun)}`], text: `${stats.marksOnGun} ${labels().stat_marks}` });
  }
  if (achievements.length) rows.push(achievements);
  return rows.slice(0, 4);
}

function directChildByClass(parent, className) {
  for (const child of parent.children) {
    if (child.classList.contains(className)) return child;
  }
  return null;
}

function renderCardStats() {
  const minimumBattles = Number(state.statsConfig?.minimumBattles ?? 1);
  const cards = Array.from(document.querySelectorAll(`[data-test-id^="${CARD_PREFIX}"]`));
  let matched = 0;
  let visible = 0;
  let sampleText = "";
  cards.forEach((card) => {
    const id = card.getAttribute("data-test-id").slice(CARD_PREFIX.length);
    const stats = state.stats?.[id];
    const nativeContent = card.querySelector('[class*="Card_content_"]');
    const staleOverlay = nativeContent ? directChildByClass(nativeContent, "hcp-card-stats") : null;
    if (staleOverlay) staleOverlay.remove();
    const host = card;
    host.classList.add("hcp-card-stats-host");
    let overlay = directChildByClass(host, "hcp-card-stats");
    if (stats) matched += 1;
    card.removeAttribute("data-hcp-stats");
    if (!stats || Number(stats.battles) < minimumBattles || state.statsConfig?.enabled === false) {
      if (overlay) overlay.remove();
      return;
    }

    if (!overlay) {
      overlay = document.createElement("div");
      overlay.className = "hcp-card-stats";
      overlay.dataset.vehicleId = id;
      host.appendChild(overlay);
    }

    const rows = statRows(stats);
    const signature = JSON.stringify(rows);
    if (overlay.dataset.signature !== signature) {
      overlay.dataset.signature = signature;
      overlay.innerHTML = "";
      rows.forEach((items) => {
        const line = document.createElement("div");
        line.className = "hcp-card-stats-line";
        items.forEach((item) => {
          const value = document.createElement("span");
          value.className = `hcp-card-stat ${item.classes.map((name) => `hcp-card-stat--${name}`).join(" ")}`;
          value.textContent = item.text;
          line.appendChild(value);
        });
        overlay.appendChild(line);
      });
    }
    if (!sampleText) sampleText = `${id}=${overlay.textContent}`;
    visible += 1;
  });

  if (!cards.length) return;
  const diagnostic = `${cards.length}/${matched}/${visible}/${Object.keys(state.stats || {}).length}`;
  if (diagnostic !== lastStatsDiagnostic) {
    lastStatsDiagnostic = diagnostic;
    debugLog(`cards/matched/visible/stats: ${diagnostic}; sample: ${sampleText}`);
  }
}

function hideTooltip() {
  if (!tooltipElement) return;
  tooltipElement.remove();
  tooltipElement = null;
}

function showTooltip(anchor, title, description) {
  hideTooltip();
  const rect = anchor.getBoundingClientRect();
  const tooltip = document.createElement("div");
  tooltip.className = "hcp-hover-tooltip";
  const titleElement = document.createElement("div");
  titleElement.className = "hcp-hover-tooltip-title";
  titleElement.textContent = title;
  tooltip.appendChild(titleElement);
  if (description) {
    const descriptionElement = document.createElement("div");
    descriptionElement.className = "hcp-hover-tooltip-description";
    String(description).split("\n").forEach((lineText, lineIndex) => {
      const line = document.createElement("div");
      line.className = "hcp-hover-tooltip-description-line";
      if (lineIndex) line.classList.add("hcp-hover-tooltip-description-line--spaced");
      line.textContent = lineText;
      descriptionElement.appendChild(line);
    });
    tooltip.appendChild(descriptionElement);
  }
  tooltip.style.left = `${Math.round(rect.right + 8)}px`;
  tooltip.style.top = `${Math.round(rect.top + rect.height / 2)}px`;
  document.body.appendChild(tooltip);
  tooltipElement = tooltip;
}

function bindTooltip(button, title, description) {
  button.addEventListener("mouseenter", () => showTooltip(button, title, description));
  button.addEventListener("mouseleave", hideTooltip);
  button.addEventListener("click", hideTooltip);
}

function addHeading(parent, text) {
  const heading = document.createElement("div");
  heading.className = "hcp-native-heading";
  if (parent.children.length) heading.classList.add("hcp-native-heading--spaced");
  heading.textContent = text;
  parent.appendChild(heading);
}

function carouselRowButtonContent(rows) {
  const automatic = Number(rows) === 0;
  const visibleRows = automatic ? 4 : Number(rows);
  const bars = [];
  for (let index = 0; index < visibleRows; index += 1) {
    bars.push(`<rect x="2" y="${2 + index * 4}" width="12" height="2" rx="0.5" style="fill:#fff!important"/>`);
  }
  return `<svg viewBox="0 0 16 18" aria-hidden="true" style="color:#fff!important;fill:#fff!important">${bars.join("")}</svg>` +
    `<span class="hcp-native-row-button-label" style="color:#fff!important">${automatic ? "A" : rows}</span>`;
}

function renderNativeFilterPanel() {
  const popover = document.querySelector('[class*="FilterPopover_popover_"]');
  if (!popover) return;
  const nativeCategories = popover.querySelectorAll('[class*="FilterPopover_category_"]');
  if (!nativeCategories.length) return;
  const nativeContent = nativeCategories[nativeCategories.length - 1].parentElement;
  if (!nativeContent) return;

  let section = popover.querySelector(".hcp-native-section");
  if (!section) {
    section = document.createElement("div");
    section.className = "hcp-native-section";
    nativeContent.appendChild(section);
  }

  const signature = JSON.stringify([
    state.filters,
    state.enabled,
    activeFilters,
    state.sorting,
    state.actionCards,
    state.carousel,
    language()
  ]);
  if (section.dataset.signature === signature) return;
  section.dataset.signature = signature;
  hideTooltip();
  section.innerHTML = "";

  addHeading(section, labels().smart_filters);
  const filters = document.createElement("div");
  filters.className = "hcp-native-filters";
  section.appendChild(filters);

  for (const filter of state.filters || []) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "hcp-native-filter";
    const isActive = filter.id === "all" ? activeFilters.length === 0 : activeFilters.includes(filter.id);
    if (isActive) button.classList.add("hcp-native-filter--active");
    button.disabled = !state.enabled;
    if (button.disabled) button.classList.add("hcp-native-control--disabled");
    button.dataset.filterId = filter.id;
    button.innerHTML = FILTER_ICONS[filter.id] || `<span>${labels()[filter.id] || filter.id}</span>`;
    button.setAttribute("aria-label", labels()[filter.id] || filter.id);
    const toggleState = isActive ? labels().toggle_on : labels().toggle_off;
    const filterName = labels()[filter.id] || filter.id;
    const filterDescription = labels()[`${filter.id}_description`] || "";
    const filterMeta = state.enabled ? `${labels().matches}: ${filter.count} · ${toggleState}` : labels().unavailable;
    button.title = `${filterName}: ${filterMeta}`;
    bindTooltip(button, filterName, `${filterDescription}\n${filterMeta}`);
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      callCommand("onToggleFilter", { id: filter.id });
    });
    filters.appendChild(button);
  }

  const refresh = document.createElement("button");
  refresh.type = "button";
  refresh.className = "hcp-native-icon-button";
  refresh.textContent = "↻";
  refresh.title = labels().refresh;
  refresh.setAttribute("aria-label", labels().refresh);
  bindTooltip(refresh, labels().refresh, labels().refresh_description);
  refresh.addEventListener("click", () => callCommand("onRefresh"));
  filters.appendChild(refresh);

  if (state.sorting?.enabled && Array.isArray(state.sorting.options)) {
    addHeading(section, labels().sorting);
    const sorting = document.createElement("div");
    sorting.className = "hcp-native-sorting";
    section.appendChild(sorting);
    for (const mode of state.sorting.options) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "hcp-native-sort-button";
      if (mode === state.sorting.mode) button.classList.add("hcp-native-sort-button--active");
      button.innerHTML = SORT_ICONS[mode] || SORT_ICONS.default;
      const title = labels()[`sort_${mode}`] || mode;
      button.setAttribute("aria-label", title);
      button.title = title;
      bindTooltip(button, title, mode === 'random' ? labels().sort_random_description : mode === state.sorting.mode && state.sorting.directional !== false
        ? (state.sorting.descending ? labels().descending : labels().ascending)
        : "");
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        callCommand("onSetSorting", { mode, descending: Boolean(state.sorting.descending) });
      });
      sorting.appendChild(button);
    }
    if (state.sorting.directional !== false) {
      const direction = document.createElement("button");
      direction.type = "button";
      direction.className = "hcp-native-sort-button hcp-native-sort-direction";
      direction.innerHTML = state.sorting.descending
        ? SORT_DIRECTION_ICONS.descending
        : SORT_DIRECTION_ICONS.ascending;
      direction.title = state.sorting.descending ? labels().descending : labels().ascending;
      bindTooltip(direction, direction.title, labels()[`sort_${state.sorting.mode}`] || state.sorting.mode);
      direction.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        callCommand("onSetSorting", {
          mode: state.sorting.mode || "default",
          descending: !Boolean(state.sorting.descending)
        });
      });
      sorting.appendChild(direction);
    }
  }

  addHeading(section, labels().carousel_rows);
  const carouselRows = document.createElement("div");
  carouselRows.className = "hcp-native-carousel-rows";
  section.appendChild(carouselRows);
  const automaticRows = state.carousel?.mode === "auto";
  const activeRows = Math.max(1, Math.min(4, Number(state.carousel?.rows || 2)));
  const supportedRows = state.carousel?.supportedRows || [1, 2, 3, 4];
  for (const rows of [0, ...supportedRows]) {
    const automatic = Number(rows) === 0;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "hcp-native-row-button";
    if ((automatic && automaticRows) || (!automatic && !automaticRows && Number(rows) === activeRows)) {
      button.classList.add("hcp-native-row-button--active");
    }
    button.innerHTML = carouselRowButtonContent(rows);
    const buttonTitle = automatic ? labels().carousel_auto : `${labels().carousel_rows}: ${rows}`;
    const buttonDescription = automatic ? labels().carousel_auto_description : labels().carousel_rows_description;
    button.setAttribute("aria-label", buttonTitle);
    button.title = buttonTitle;
    bindTooltip(button, buttonTitle, buttonDescription);
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      callCommand("onSetCarouselRows", { rows: Number(rows) });
    });
    carouselRows.appendChild(button);
  }
}

function syncModel() {
  const model = findModel();
  if (!model) return;
  const stateJson = String(unwrap(model.stateJson) || "{}");
  const nextActiveFiltersJson = String(unwrap(model.activeFiltersJson) || "[]");
  if (stateJson === lastStateJson &&
      nextActiveFiltersJson === lastActiveFiltersJson) return;
  lastStateJson = stateJson;
  lastActiveFiltersJson = nextActiveFiltersJson;
  try {
    state = JSON.parse(stateJson);
  } catch (error) {
    console.error("[HangarCarouselPlus] Invalid state JSON", error);
    state = { filters: [], stats: {}, statsConfig: {}, sorting: {}, actionCards: {}, carousel: { rows: 2 }, enabled: false };
  }
  try {
    activeFilters = JSON.parse(nextActiveFiltersJson);
    if (!Array.isArray(activeFilters)) activeFilters = [];
  } catch (error) {
    console.error("[HangarCarouselPlus] Invalid active filters JSON", error);
    activeFilters = [];
  }
  scheduleRender();
}

engine.whenReady.then(() => {
  const observer = new MutationObserver((mutations) => {
    if (mutations.some(mutationAffectsHcp)) scheduleRender();
  });
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["data-test-id"]
  });
  window.engine.on("subViews.onAdded", syncModel);
  window.setInterval(syncModel, 500);
  syncModel();
  scheduleRender();
});
