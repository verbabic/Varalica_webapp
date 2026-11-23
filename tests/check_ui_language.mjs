import fs from "node:fs";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../static/i18n.js", import.meta.url), "utf8");

function load({ saved = null, languages = ["hr"] } = {}) {
  const store = { varalica_ui_language: saved };
  const context = {
    localStorage: {
      getItem(key) {
        return store[key] ?? null;
      },
      setItem(key, value) {
        store[key] = value;
      },
    },
    navigator: { languages, language: languages[0] || "" },
    document: {
      documentElement: {},
      title: "",
      querySelector() {
        return { setAttribute() {} };
      },
      querySelectorAll() {
        return [];
      },
    },
    window: {},
  };
  vm.createContext(context);
  vm.runInContext(source, context);
  return { i18n: context.window.VaralicaI18n, store };
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) {
    throw new Error(`${label}: expected ${expected}, got ${actual}`);
  }
}

const saved = load({ saved: "de", languages: ["hr-HR"] });
assertEqual(saved.i18n.language, "de", "saved preference");

const austrian = load({ languages: ["de-AT", "en"] });
assertEqual(austrian.i18n.language, "de", "de-AT");

const serbian = load({ languages: ["en-US", "sr-RS"] });
assertEqual(serbian.i18n.language, "sr", "sr-RS");

const croatian = load({ languages: ["hr-HR"] });
assertEqual(croatian.i18n.language, "hr", "hr-HR");

const fallback = load({ languages: ["fr-FR", "en"] });
assertEqual(fallback.i18n.language, "hr", "fallback");

const manual = load({ languages: ["de-DE"] });
manual.i18n.setUiLanguage("sr", { manual: true });
assertEqual(manual.store.varalica_ui_language, "sr", "manual storage");
assertEqual(manual.i18n.t("mode.chat"), "Chat", "chat name");
assertEqual(manual.i18n.t("home.title"), "Varalica", "serbian title");
manual.i18n.setUiLanguage("de", { manual: true });
assertEqual(manual.i18n.t("home.title"), "Betrüger", "german title");
assertEqual(manual.i18n.t("room.round_label", { round_number: 3 }), "Runde 3", "placeholder");
assertEqual(
  manual.i18n.translateServerMessage("Host je napravio Chat sobu."),
  "Der Spielleiter hat einen Raum im Modus Chat erstellt.",
  "mode lock",
);

console.log("ui language checks passed");
