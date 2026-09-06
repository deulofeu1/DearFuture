(() => {
  const messages = {
    zh: {
      "page.homeTitle": "DearFuture — 把担忧寄给未来",
      "page.detailTitle": "DearFuture — 一封寄给未来的信",
      "nav.send": "寄一封信",
      "nav.wall": "慢递信墙",
      "nav.back": "返回慢递信墙",
      "nav.language": "CN",
      "brand.subtitle": "未来慢递",
      "hero.title": "把今天的担忧，",
      "hero.emphasis": "寄给未来。",
      "hero.intro":
        "有些担心不必急着回答。把它交给慢递蜗牛，等约定的日子到了，它会带着后来发生的故事，慢慢走回来。",
      "hero.action": "写下我的问题",
      "postcard.greeting": "亲爱的过去的我：",
      "postcard.quote": "“你担心的事情，后来真的发生了吗？”",
      "postcard.reply": "现实会慢慢回信。",
      "stats.sent": "寄出的心事",
      "stats.traveling": "正在慢慢赶路",
      "stats.arrived": "回信已经送达",
      "stats.happened": "后来真的发生",
      "form.title": "把一件担心，交给时间",
      "form.intro": "我们会替你收好这封信，在约定的日子看看后来发生了什么。",
      "form.question": "你的问题",
      "form.questionPlaceholder":
        "例如：一年以后，我现在担心的工作变化真的发生了吗？",
      "form.date": "想在哪一天收到？",
      "form.period": "约在哪个时刻？",
      "form.submit": "交给慢递蜗牛",
      "form.past": "这个时刻已经轻轻走过去了，请和小蜗牛约一个未来的时刻。",
      "form.processing1": "🐌 小蜗牛正在替你封好信封……",
      "form.processing2": "🕯️ 它正在把你的心事写上地址，准备出发……",
      "form.processing3": "🌿 信已经收好啦，小蜗牛正在踏上慢慢的旅程……",
      "form.failed": "这封信暂时没有寄出去，请稍后再试",
      "form.successPublic": "已经交给慢递蜗牛。",
      "form.journey": "看看它的旅程",
      "form.successPrivate":
        "已经交给慢递蜗牛。这封信只属于你，可以在专属页面等待未来回信。",
      "wall.title": "一些正在路上的心事",
      "wall.filter": "按分类筛选",
      "wall.all": "全部分类",
      "wall.empty": "信墙还是空的。也许第一封慢递，可以从你的心事开始。",
      "wall.error": "慢递信墙正在晒太阳，请过一会儿再来看看。",
      "wall.sent": "{date} 寄出 · 约定{arrival}拆信",
      "wall.open": "拆开回信",
      "wall.track": "看看它走到哪里了",
      "footer.line": "给焦虑一点时间，未来会慢慢回信。",
      "period.morning": "清晨 · 08:00",
      "period.noon": "正午 · 12:00",
      "period.afternoon": "午后 · 15:00",
      "period.dusk": "黄昏 · 18:00",
      "period.night": "入夜 · 21:00",
      "time.arrival": "{date}的{period}",
      "category.technology": "科技与变化",
      "category.career": "工作与成长",
      "category.weather": "天气与自然",
      "category.society": "生活与世界",
      "category.finance": "金钱与市场",
      "category.general": "一件心事",
      "status.resolved": "💌 来自未来的回信已送达",
      "status.verifying": "🐌 已抵达未来，正在四处看看",
      "status.retry": "🌫️ 路上有一点雾，稍后继续出发",
      "status.failed": "🧭 这封信暂时迷路了",
      "status.scheduled": "🐌 正在前往{arrival}",
      "outcome.happened": "它后来真的发生了",
      "outcome.partial": "它有一部分成为了现实",
      "outcome.notHappened": "它并没有像担心的那样发生",
      "outcome.uncertain": "未来暂时还没有说清楚",
      "outcome.fallback": "未来寄来了一些新的线索",
      "detail.loading": "🐌 正在轻轻打开这只信封……",
      "detail.about": "一封关于「{category}」的慢递",
      "detail.sent": "{date} 寄出",
      "detail.promised": "约定{arrival}拆信",
      "detail.note": "一封来自未来的回信",
      "detail.salutation": "亲爱的过去的你：",
      "detail.sources": "想看看小蜗牛沿途去了哪里？",
      "detail.noSources": "未来还没有留下足够清楚的线索，再给它一点时间吧。",
      "detail.share": "把这封信分享给朋友",
      "detail.copied": "这封信的地址已经复制好啦",
      "detail.notFound":
        "这只信封没有贴在公开信墙上，也许它选择了安静地保守秘密。",
      "detail.home": "回到慢递小屋",
      "journey.scheduledTitle": "小蜗牛已经背上信封",
      "journey.scheduledText":
        "它会慢慢走到约定的日子，再替你看看后来发生了什么。",
      "journey.verifyingTitle": "小蜗牛已经抵达未来",
      "journey.verifyingText": "它正在四处走走，听听世界如何回答你当时的担心。",
      "journey.retryTitle": "路上遇到了一点雾",
      "journey.retryText": "别担心，小蜗牛休息一下，认清方向后还会继续出发。",
      "journey.failedTitle": "这封信暂时迷路了",
      "journey.failedText": "我们已经记下它，会继续照看这段没有走完的旅程。",
      "journey.expected": "预计在{arrival}抵达",
    },
    en: {
      "page.homeTitle": "DearFuture — Send your worries to tomorrow",
      "page.detailTitle": "DearFuture — A letter to tomorrow",
      "nav.send": "Send a letter",
      "nav.wall": "Slow Mail Wall",
      "nav.back": "Back to the Slow Mail Wall",
      "nav.language": "EN",
      "brand.subtitle": "Slow Mail",
      "hero.title": "Send today's worries",
      "hero.emphasis": "to tomorrow.",
      "hero.intro":
        "Some worries do not need an answer today. Hand yours to our little mail snail, and it will return with a story when the promised day arrives.",
      "hero.action": "Write my question",
      "postcard.greeting": "DEAR PAST ME,",
      "postcard.quote": "“Did the thing you feared ever happen?”",
      "postcard.reply": "Reality will write back.",
      "stats.sent": "Worries sent",
      "stats.traveling": "Still on their way",
      "stats.arrived": "Replies delivered",
      "stats.happened": "Eventually happened",
      "form.title": "Give a worry to time",
      "form.intro":
        "We will keep your letter safe and revisit it on the promised day.",
      "form.question": "Your question",
      "form.questionPlaceholder":
        "For example: A year from now, will the change at work I fear have actually happened?",
      "form.date": "Which day should it arrive?",
      "form.period": "At what time of day?",
      "form.submit": "Give it to the mail snail",
      "form.past":
        "That moment has already drifted by. Please choose a moment in the future.",
      "form.processing1": "🐌 The little mail snail is sealing your envelope…",
      "form.processing2": "🕯️ It is writing the address for your worry and preparing to leave…",
      "form.processing3": "🌿 Your letter is safe. The little snail is beginning its gentle journey…",
      "form.failed":
        "This letter could not leave just yet. Please try again soon.",
      "form.successPublic": "Your letter is with the mail snail.",
      "form.journey": "Follow its journey",
      "form.successPrivate":
        "Your letter is with the mail snail. It will remain yours alone on its private journey page.",
      "wall.title": "Worries currently on their way",
      "wall.filter": "Filter by category",
      "wall.all": "All categories",
      "wall.empty":
        "The wall is quiet for now. Perhaps its first slow letter could begin with you.",
      "wall.error":
        "The Slow Mail Wall is sunbathing. Please come back in a little while.",
      "wall.sent": "Sent {date} · To be opened {arrival}",
      "wall.open": "Open the reply",
      "wall.track": "See where it is",
      "footer.line": "Give worry a little time. Tomorrow will write back.",
      "period.morning": "morning · 08:00",
      "period.noon": "noon · 12:00",
      "period.afternoon": "afternoon · 15:00",
      "period.dusk": "dusk · 18:00",
      "period.night": "nightfall · 21:00",
      "time.arrival": "{period} on {date}",
      "category.technology": "Technology & Change",
      "category.career": "Work & Growth",
      "category.weather": "Weather & Nature",
      "category.society": "Life & the World",
      "category.finance": "Money & Markets",
      "category.general": "A Private Thought",
      "status.resolved": "💌 A reply from tomorrow has arrived",
      "status.verifying": "🐌 The snail has arrived and is looking around",
      "status.retry": "🌫️ A little fog on the road — the journey will continue",
      "status.failed": "🧭 This letter has temporarily lost its way",
      "status.scheduled": "🐌 On its way to {arrival}",
      "outcome.happened": "It really did happen",
      "outcome.partial": "Part of it became real",
      "outcome.notHappened": "It did not happen the way you feared",
      "outcome.uncertain": "Tomorrow has not given a clear answer yet",
      "outcome.fallback": "Tomorrow sent back a few new clues",
      "detail.loading": "🐌 Gently opening this envelope…",
      "detail.about": "A slow letter about “{category}”",
      "detail.sent": "Sent {date}",
      "detail.promised": "Promised for {arrival}",
      "detail.note": "A NOTE FROM TOMORROW",
      "detail.salutation": "Dear past you,",
      "detail.sources":
        "Want to see where the mail snail stopped along the way?",
      "detail.noSources":
        "Tomorrow has not left enough clear clues yet. Give it a little more time.",
      "detail.share": "Share this letter with a friend",
      "detail.copied": "The address of this letter has been copied",
      "detail.notFound":
        "This envelope is not on the public wall. Perhaps it chose to keep its secret quietly.",
      "detail.home": "Return to the slow mail house",
      "journey.scheduledTitle": "The little snail has shouldered your envelope",
      "journey.scheduledText":
        "It will travel slowly to the promised day, then look around and see what became of your worry.",
      "journey.verifyingTitle": "The little snail has reached tomorrow",
      "journey.verifyingText":
        "It is wandering around and listening for the world's answer to your old worry.",
      "journey.retryTitle": "There is a little fog on the road",
      "journey.retryText":
        "Do not worry. The snail will rest, find its bearings, and continue.",
      "journey.failedTitle": "This letter has temporarily lost its way",
      "journey.failedText":
        "We have made a note of it and will keep watching over its unfinished journey.",
      "journey.expected": "Expected to arrive {arrival}",
    },
  };

  let language =
    localStorage.getItem("dearfuture-language") === "en" ? "en" : "zh";
  let titleKey = null;

  function t(key, values = {}) {
    let text = messages[language][key] || messages.zh[key] || key;
    Object.entries(values).forEach(([name, value]) => {
      text = text.replaceAll(`{${name}}`, value);
    });
    return text;
  }

  function applyStaticText() {
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
    if (titleKey) document.title = t(titleKey);
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = t(node.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
      node.placeholder = t(node.dataset.i18nPlaceholder);
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((node) => {
      node.setAttribute("aria-label", t(node.dataset.i18nAria));
    });
  }

  function setLanguage(nextLanguage) {
    language = nextLanguage === "en" ? "en" : "zh";
    localStorage.setItem("dearfuture-language", language);
    applyStaticText();
    window.dispatchEvent(new CustomEvent("dearfuture:languagechange"));
  }

  function init(nextTitleKey) {
    titleKey = nextTitleKey;
    document.querySelectorAll("[data-language-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        setLanguage(language === "zh" ? "en" : "zh");
      });
    });
    applyStaticText();
  }

  function formatDate(value, long = false) {
    return new Intl.DateTimeFormat(language === "zh" ? "zh-CN" : "en-US", {
      year: "numeric",
      month: long ? "long" : "short",
      day: "numeric",
    }).format(new Date(value));
  }

  window.DearFutureI18n = {
    t,
    init,
    formatDate,
    get language() {
      return language;
    },
  };
})();
