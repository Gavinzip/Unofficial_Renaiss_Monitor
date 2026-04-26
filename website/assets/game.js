    const INTEL_LANG_STORAGE_KEY = "intel_ui_lang";
    const uiTextNodeCache = new WeakMap();
    const uiTranslationMemo = new Map();
    let uiTranslateVersion = 0;
    const GAME_UI_TRANSLATIONS = {
      "zh-Hans": {
            "Renaiss World | Immersive RPG Showcase": "Renaiss World | Immersive RPG Showcase",
            "Renaiss": "Renaiss",
            "Back": "Back",
            "世界觀": "世界观",
            "介紹": "介绍",
            "玩法": "玩法",
            "氣候": "气候",
            "前往": "前往",
            "官網": "官网",
            "Choice-Driven Open World RPG": "选择驱动开放世界 RPG",
            "World": "World",
            "選擇你的": "选择你的",
            "未來": "未来",
            "帶著夥伴走進一個因你而改變的世界。": "带著伙伴走进一个因你而改变的世界。",
            "文字 RPG 遊戲": "文字 RPG 游戏",
            "立即看玩法": "立即看玩法",
            "先讀世界觀": "先读世界观",
            "向下滑，進入世界": "向下滑，进入世界",
            "世界觀 / The World Behind The Routes": "世界观 / The World Behind The Routes",
            "你身在 Renaiss 海域。這片星域長年由 Renaiss 維運，是航道、交易與居住秩序的核心。": "你身在 Renaiss 海域。这片星域长年由 Renaiss 维运，是航道、交易与居住秩序的核心。",
            "World Lore": "世界观",
            "但在明面秩序之外，另一股勢力正與既有體系長期角力。它們在各區節點滲透、造假、放出低價誘惑，試著把來源、鑑定與信任一點一點拆掉。": "但在明面秩序之外，另一股势力正与既有体系长期角力。它们在各区节点渗透、造假、放出低价诱惑，试著把来源、鑑定与信任一点一点拆掉。",
            "所以在": "所以在 ",
            "Renaiss World": "Renaiss World",
            "裡，你和夥伴不是只去探險。你是在調查來源、守住真偽、拆穿供應鏈裡的假象；每一次探索、交易、戰鬥、撤退，都會改寫下一段劇情。": "里，你和伙伴不是只去探险。你是在调查来源、守住真伪、拆穿供应链里的假象；每一次探索、交易、战斗、撤退，都会改写下一段剧情。",
            "這是開放世界，沒有固定主線按鈕。章節、流言、戰況與角色命運都由你的選擇被動推進，最後變成所有玩家都看得見的長期傳聞。": "这是开放世界，没有固定主线按钮。章节、流言、战况与角色命运都由你的选择被动推进，最后变成所有玩家都看得见的长期传闻。",
            "Game Intro": "游戏介绍",
            "遊戲介紹": "游戏介绍",
            "這是一個把選擇、夥伴、回合制戰鬥、鍛裝與交易一路串起來的文字 RPG。你不是在看世界運轉，而是在把自己的路一格一格打出來。": "这是一个把选择、伙伴、回合制战斗、锻装与交易一路串起来的文字 RPG。你不是在看世界运转，而是在把自己的路一格一格打出来。",
            "從第一隻夥伴開始，慢慢養出自己的配招、戰線與傳聞": "从第一只伙伴开始，慢慢养出自己的配招、战线与传闻",
            "你會先拿到夥伴和第一批技能，接著在回合制戰鬥裡磨出節奏，在導師與市場裡補齊關鍵招式，再把戰利品鍛成新裝，最後一路推進六大主地區。": "你会先拿到伙伴和第一批技能，接著在回合制战斗里磨出节奏，在导师与市场里补齐关键招式，再把战利品锻成新装，最后一路推进六大主地区。",
            "世界分歧": "世界分歧",
            "夥伴配招": "伙伴配招",
            "回合制對戰": "回合制对战",
            "AI 鍛裝": "AI 锻装",
            "六地主線": "六地主线",
            "Intro 01": "Intro 01",
            "選擇未來": "选择未来",
            "AI 劇情": "AI 剧情",
            "分歧路線": "分歧路线",
            "不是看劇情分支，是親手把下一章推向別的方向": "不是看剧情分支，是亲手把下一章推向别的方向",
            "調查、交涉、戰鬥、撤退，每個決定都會把後面的事件改寫。你怎麼出手，世界就怎麼回應。": "调查、交涉、战斗、撤退，每个决定都会把后面的事件改写。你怎么出手，世界就怎么回应。",
            "你留下的痕跡，會回來找你：": "你留下的痕迹，会回来找你：",
            "剛剛那一步，可能在下一段事件、下一場戰鬥，甚至更後面的局勢裡現身。": "刚刚那一步，可能在下一段事件、下一场战斗，甚至更后面的局势里现身。",
            "同一場局面，可以走成不同命運：": "同一场局面，可以走成不同命运：",
            "你可以硬闖、周旋、繞路或收手，世界回給你的後續也會完全不同。": "你可以硬闯、周旋、绕路或收手，世界回给你的后续也会完全不同。",
            "世界不是照劇本走，是照你留下的痕跡走": "世界不是照剧本走，是照你留下的痕迹走",
            "你做過的事不會消失，它只會在更後面的地方重新出現。": "你做过的事不会消失，它只会在更后面的地方重新出现。",
            "Intro 02": "Intro 02",
            "水火草起始": "水火草起始",
            "技能晶片": "技能晶片",
            "自由配招": "自由配招",
            "寵物配技能，組出你的專屬配招": "宠物配技能，组出你的专属配招",
            "起點只有水、火、草三種，但真正的差別在後面。技能晶片一張張學進去之後，同一隻夥伴也能走成完全不同的戰法。": "起点只有水、火、草三种，但真正的差别在后面。技能晶片一张张学进去之后，同一只伙伴也能走成完全不同的战法。",
            "起始屬性先決定開場手感：": "起始属性先决定开场手感：",
            "水、火、草三種起步，會把你的前期節奏直接帶向不同方向。": "水、火、草三种起步，会把你的前期节奏直接带向不同方向。",
            "技能晶片會把同一隻夥伴養出不同個性：": "技能晶片会把同一只伙伴养出不同个性：",
            "有人走爆發，有人走牽制，也有人把續戰和反打養成招牌。": "有人走爆发，有人走牵制，也有人把续战和反打养成招牌。",
            "第一隻夥伴，就能長成你的代表作": "第一只伙伴，就能长成你的代表作",
            "不是抽到別隻才有差，而是你怎麼養，牠就會怎麼打。": "不是抽到别只才有差，而是你怎么养，牠就会怎么打。",
            "Intro 03": "Intro 03",
            "回合制": "回合制",
            "速度定先手": "速度定先手",
            "屬性玩法": "属性玩法",
            "回合制戰鬥裡，先手、屬性與技能配置會一起決定你的勝法": "回合制战斗里，先手、属性与技能配置会一起决定你的胜法",
            "這不是自動對轟。誰先出手、用哪個屬性切進去、五格技能怎麼排，會把每一場戰鬥拉成完全不同的節奏。": "这不是自动对轰。谁先出手、用哪个属性切进去、五格技能怎么排，会把每一场战斗拉成完全不同的节奏。",
            "速度決定先手：": "速度决定先手：",
            "先比招式速度，同速再比夥伴本身速度，真的一樣才會擲硬幣搶先手。": "先比招式速度，同速再比伙伴本身速度，真的一样才会掷硬币抢先手。",
            "屬性玩法：": "属性玩法：",
            "水剋火、火剋草、草剋水；液態偏牽制與回補，熱能偏爆發與灼燒，生質偏綁定、護盾與續戰。": "水剋火、火剋草、草剋水；液态偏牵制与回补，热能偏爆发与灼烧，生质偏绑定、护盾与续战。",
            "夥伴可裝備 5 個技能：": "伙伴可装备 5 个技能：",
            "起手、控場、反打、壓軸都由你自己選，T1 到 T3 的節奏也由你自己排。": "起手、控场、反打、压轴都由你自己选，T1 到 T3 的节奏也由你自己排。",
            "技能獲取：": "技能获取：",
            "開局免費五連抽會先送你第一批技能，導師戰贏了有機會直接傳招，玩家賣場則能讓你補齊想要的關鍵技能。": "开局免费五连抽会先送你第一批技能，导师战赢了有机会直接传招，玩家卖场則能让你补齐想要的关键技能。",
            "真正上頭的地方，是你終於組出那套一出手就知道是你的配招": "真正上头的地方，是你终于组出那套一出手就知道是你的配招",
            "當速度、控制、爆發和保命咬在一起，你的打法才會真的成形。": "当速度、控制、爆发和保命咬在一起，你的打法才会真的成形。",
            "Intro 04": "Intro 04",
            "敵人戰": "敌人战",
            "導師戰": "导师战",
            "好友戰": "好友战",
            "敵人戰推主線，導師戰傳招，好友戰專打配招理解": "敌人战推主线，导师战传招，好友战专打配招理解",
            "三種戰鬥，不是同一個介面換名字。你進的是不同戰線，拿回來的成長也完全不同。": "三种战斗，不是同一个介面换名字。你进的是不同战线，拿回来的成长也完全不同。",
            "敵人戰：": "敌人战：",
            "把路打開，把資源帶回來，也把後面的風險和故事一起往前推。": "把路打开，把资源带回来，也把后面的风险和故事一起往前推。",
            "導師戰：": "导师战：",
            "把導師壓到指定血線就算通過考驗，贏下來還有機會把導師的招式學進自己隊伍。": "把导师压到指定血线就算通过考验，赢下来还有机会把导师的招式学进自己队伍。",
            "好友戰：": "好友战：",
            "不掉金幣、不上通緝、不碰生死，純粹比你的配招理解和對手到底誰更完整。": "不掉金币、不上通缉、不碰生死，纯粹比你的配招理解和对手到底谁更完整。",
            "同樣是打，拿回來的東西卻完全不同": "同样是打，拿回来的东西却完全不同",
            "有人拿資源，有人拿新招，有人拿到的是一場真正驗證自己構築的對局。": "有人拿资源，有人拿新招，有人拿到的是一场真正验证自己构筑的对局。",
            "Intro 05": "Intro 05",
            "裝備融合": "装备融合",
            "玩家賣場": "玩家卖场",
            "資源流動": "资源流动",
            "三件藏品入爐，AI 會替你鍛出一件全新的裝備": "三件藏品入炉，AI 会替你锻出一件全新的装备",
            "這裡的裝備不是固定掉落表。你丟進三件藏品，AI 會回你一件新裝，連名字、稀有度、價值與欄位都可能是第一次出現。": "这里的装备不是固定掉落表。你丢进三件藏品，AI 会回你一件新装，连名字、稀有度、价值与栏位都可能是第一次出现。",
            "鍛裝有明確規則：": "锻装有明确规則：",
            "只有藏品能入爐，技能晶片不會被拿去亂融。": "只有藏品能入炉，技能晶片不会被拿去乱融。",
            "每次開鍛都像在等世界替你命名：": "每次开锻都像在等世界替你命名：",
            "AI 會重新組合名稱、稀有度、價值與欄位，不照固定配方出牌。": "AI 会重新组合名称、稀有度、价值与栏位，不照固定配方出牌。",
            "賣場讓資源繼續流動：": "卖场让资源继续流动：",
            "你用不到的戰利品和技能晶片，可以變成下一個人正缺的核心零件。": "你用不到的战利品和技能晶片，可以变成下一个人正缺的核心零件。",
            "每次融合，都像在看這個世界會替你寫出什麼新名字": "每次融合，都像在看这个世界会替你写出什么新名字",
            "戰利品不只會留在背包裡，它還可能變成你下一件主力。": "战利品不只会留在背包里，它还可能变成你下一件主力。",
            "Intro 06": "Intro 06",
            "六大地區": "六大地区",
            "通緝壓力": "通缉压力",
            "Boss 戰線": "Boss 战线",
            "六大主地區一路往深處打開，每一區都像新的主線入口": "六大主地区一路往深处打开，每一区都像新的主线入口",
            "中原核心、西域沙海、南疆水網、北境高原、群島航線、隱秘深域，各有自己的勢力、節奏與壓力。你每進一區，世界就會再往深處打開一層。": "中原核心、西域沙海、南疆水网、北境高原、群岛航线、隐秘深域，各有自己的势力、节奏与压力。你每进一区，世界就会再往深处打开一层。",
            "不是換背景，是換一套生存規則：": "不是换背景，是换一套生存规則：",
            "每往前一步，節奏、敵人和代價都會變得更重。": "每往前一步，节奏、敌人和代价都会变得更重。",
            "通緝、敵對勢力與 Boss 壓力會一路跟著你擴張：": "通缉、敌对势力与 Boss 压力会一路跟著你扩张：",
            "你走到哪裡，戰線就長到哪裡。": "你走到哪里，战线就长到哪里。",
            "你以為自己只是在往前走，其實是在越走越深": "你以为自己只是在往前走，其实是在越走越深",
            "每推開一個地區，你拿到的不是下一張圖，而是下一段更重、更深的主線。": "每推开一个地区，你拿到的不是下一张图，而是下一段更重、更深的主线。",
            "New Player Guide": "New Player Guide",
            "新手教學": "新手教学",
            "從 /start 到第一隻夥伴、第一套配招、第一場真正會讓你上頭的戰鬥，進場比你想的更快。": "从 /start 到第一只伙伴、第一套配招、第一场真正会让你上头的战斗，进场比你想的更快。",
            "先拿到夥伴和技能，再讓世界自己把你拖進去": "先拿到伙伴和技能，再让世界自己把你拖进去",
            "語言、角色、夥伴、五連抽很快就會到手；剩下的樂趣，是你開始想下一套配招、下一場導師戰、下一個地區。": "语言、角色、伙伴、五连抽很快就会到手；剩下的乐趣，是你开始想下一套配招、下一场导师战、下一个地区。",
            "/start 開門": "/start 开门",
            "錢包同步": "钱包同步",
            "夥伴誕生": "伙伴诞生",
            "五連抽": "五连抽",
            "主線展開": "主线展开",
            "Step 01": "Step 01",
            "Discord": "Discord",
            "/start": "/start",
            "立即開始": "立即开始",
            "打一個 /start，你的世界線就會立刻打開": "打一个 /start，你的世界线就会立刻打开",
            "在 Discord 輸入": "在 Discord 输入",
            "，系統就會立刻替你開出專屬討論串。不是先看一堆選單，而是直接讓你的冒險開始運轉。": "，系统就会立刻替你开出专属讨论串。不是先看一堆选单，而是直接让你的冒险开始运转。",
            "不用找半天入口：": "不用找半天入口：",
            "指令一打，門就開了。": "指令一打，门就开了。",
            "進去之後，世界會自己展開：": "进去之后，世界会自己展开：",
            "角色、夥伴與後面的戰線，會依序在你面前打開。": "角色、伙伴与后面的战线，会依序在你面前打开。",
            "先走進去，世界才會開始回應你": "先走进去，世界才会开始回应你",
            "這個遊戲最好的介紹，不在門外，而是在你按下 /start 之後。": "这个游戏最好的介绍，不在门外，而是在你按下 /start 之后。",
            "Step 02": "Step 02",
            "BSC 錢包": "BSC 钱包",
            "背景同步": "背景同步",
            "可領 RNS": "可领 RNS",
            "錢包先接上，資產與可領 RNS 會在背景裡慢慢補進來": "钱包先接上，资产与可领 RNS 会在背景里慢慢补进来",
            "這一步不是卡關，而是把鏈上資產接進你的世界。地址現在先填，角色建好後才正式綁定；同步完成後，可領 RNS 會自動入帳，你不用停下來等。": "这一步不是卡关，而是把链上资产接进你的世界。地址现在先填，角色建好后才正式绑定；同步完成后，可领 RNS 会自动入帐，你不用停下来等。",
            "現在填先暫存，建角後才正式綁定：": "现在填先暂存，建角后才正式绑定：",
            "不想現在處理也能先跳過，之後到設定再補。": "不想现在处理也能先跳过，之后到设定再补。",
            "RNS 有明確換算規則：": "RNS 有明确换算规則：",
            "目前按開包與市場買入的總花費 × 0.5 計入可領 RNS。": "目前按开包与市场买入的总花费 × 0.5 计入可领 RNS。",
            "先接上，後面的經濟就會慢慢跟上你": "先接上，后面的经济就会慢慢跟上你",
            "這不是把你卡在門口，而是先把鏈上資產接進你的冒險。": "这不是把你卡在门口，而是先把链上资产接进你的冒险。",
            "Step 03": "Step 03",
            "建立角色": "建立角色",
            "命名角色": "命名角色",
            "冒險入口": "冒险入口",
            "給自己一個名字，讓世界開始記得你": "给自己一个名字，让世界开始记得你",
            "角色一旦命名，這個世界就不再把你當過客。故事會開始用你的名字開口，後面的選擇也會真的變成你的事。": "角色一旦命名，这个世界就不再把你当过客。故事会开始用你的名字开口，后面的选择也会真的变成你的事。",
            "從這一步開始，你不再是旁觀者：": "从这一步开始，你不再是旁观者：",
            "世界會把你算進它自己的秩序裡。": "世界会把你算进它自己的秩序里。",
            "你的名字會被帶進後面的事件裡：": "你的名字会被带进后面的事件里：",
            "之後的路，會開始真正和你綁在一起。": "之后的路，会开始真正和你绑在一起。",
            "名字落下去的那一刻，你就不是旁觀者了": "名字落下去的那一刻，你就不是旁观者了",
            "從這一步開始，冒險不再發生在別人身上，而是發生在你身上。": "从这一步开始，冒险不再发生在别人身上，而是发生在你身上。",
            "Step 04": "Step 04",
            "孵化寵物": "孵化宠物",
            "夥伴同行": "伙伴同行",
            "選擇你的第一隻夥伴": "选择你的第一只伙伴",
            "水、火、草三種起始夥伴，決定的是你最初的節奏與氣質。再替牠取名，這隻夥伴就會陪你走進第一段故事、第一場戰鬥，還有後面的每一套配招。": "水、火、草三种起始伙伴，决定的是你最初的节奏与气质。再替牠取名，这只伙伴就会陪你走进第一段故事、第一场战斗，还有后面的每一套配招。",
            "起始屬性一變，開場手感就跟著變：": "起始属性一变，开场手感就跟著变：",
            "你的第一套打法，從這一刻就已經決定一半。": "你的第一套打法，从这一刻就已经决定一半。",
            "第一隻夥伴不是過場：": "第一只伙伴不是过场：",
            "它會陪你把第一套戰法從雛形養成真正的主力。": "它会陪你把第一套战法从雏形养成真正的主力。",
            "很多人愛上這個世界，就是從第一隻夥伴開始": "很多人爱上这个世界，就是从第一只伙伴开始",
            "當你替牠取完名字，這場冒險通常就真的開始有感覺了。": "当你替牠取完名字，这场冒险通常就真的开始有感觉了。",
            "Step 05": "Step 05",
            "免費五連抽": "免费五连抽",
            "配招成形": "配招成形",
            "五連抽一開，第一套能改變打法的技能就會落進你手裡": "五连抽一开，第一套能改变打法的技能就会落进你手里",
            "夥伴孵化完成後，系統會直接送上免費五連抽。晶片會留在背包裡，等你學進夥伴、掛上賣場，或替下一套配招先埋伏筆。": "伙伴孵化完成后，系统会直接送上免费五连抽。晶片会留在背包里，等你学进伙伴、挂上卖场，或替下一套配招先埋伏笔。",
            "開場就有技能能玩：": "开场就有技能能玩：",
            "你不用等很久，第一套配招很快就會開始成形。": "你不用等很久，第一套配招很快就会开始成形。",
            "晶片是真的資產，不是一閃而過的演出：": "晶片是真的资产，不是一闪而过的演出：",
            "它會留在你手上，等你拿去學、拿去賣，或等下一隻夥伴來用。": "它会留在你手上，等你拿去学、拿去卖，或等下一只伙伴来用。",
            "第一批技能一到手，你就會開始想下一套配招": "第一批技能一到手，你就会开始想下一套配招",
            "這不是暖身，它就是你第一批真正能改變打法的戰力。": "这不是暖身，它就是你第一批真正能改变打法的战力。",
            "Step 06": "Step 06",
            "主選單": "主选单",
            "玩法展開": "玩法展开",
            "一路解鎖": "一路解锁",
            "主選單一開，整個世界才正式展開": "主选单一开，整个世界才正式展开",
            "故事、地圖、戰鬥、背包、融合、賣場、導師切磋與好友戰，會隨著你的進度一層層展開。你不用一次學完，只要先讓自己走進去。": "故事、地图、战斗、背包、融合、卖场、导师切磋与好友战，会随著你的进度一层层展开。你不用一次学完，只要先让自己走进去。",
            "規則不會一次塞滿：": "规則不会一次塞满：",
            "你先往前走，該出現的玩法會在對的時候出現。": "你先往前走，该出现的玩法会在对的时候出现。",
            "深度會追著你長出來：": "深度会追著你长出来：",
            "你每往前玩一步，這個世界就會再多一層可以碰的東西。": "你每往前玩一步，这个世界就会再多一层可以碰的东西。",
            "真正讓人停不下來的，是世界會越玩越大": "真正让人停不下来的，是世界会越玩越大",
            "你每往前走一步，新的玩法和新的壓力就會自己長出來。": "你每往前走一步，新的玩法和新的压力就会自己长出来。",
            "Climate States": "气候状态",
            "動態氣候 / Dynamic Climate": "动态气候 / Dynamic Climate",
            "這不是背景換色，而是同一個世界在四種氣候裡露出四種節奏。晴空讓你推進，降雨帶來變數，旱象逼你精算，降雪把每一步都壓得更重。": "这不是背景换色，而是同一个世界在四种气候里露出四种节奏。晴空让你推进，降雨带来变数，旱象逼你精算，降雪把每一步都压得更重。",
            "同一條路，氣候一變，打法就跟著變。": "同一条路，气候一变，打法就跟著变。",
            "晴空 / Clear Sky · 推進期": "晴空 / Clear Sky · 推进期",
            "視野乾淨，節奏平穩，適合推主線、探圖、整理資源，像替下一段冒險先鋪好路。": "视野乾净，节奏平稳，适合推主线、探图、整理资源，像替下一段冒险先铺好路。",
            "降雨 / Rainfall · 變數期": "降雨 / Rainfall · 变数期",
            "光線、路面與事件節奏都開始變動，適合快推、快收、快離場，每一步都更講究判斷。": "光线、路面与事件节奏都开始变动，适合快推、快收、快离场，每一步都更讲究判断。",
            "旱象 / Drought · 緊縮期": "旱象 / Drought · 紧缩期",
            "補給與撤退都變得尖銳，錯一步就會被放大。這種氣候會逼你把每個選擇算得更狠。": "补给与撤退都变得尖锐，错一步就会被放大。这种气候会逼你把每个选择算得更狠。",
            "降雪 / Snowfall · 試煉期": "降雪 / Snowfall · 试炼期",
            "節奏放慢、能見度壓低，但也讓每一步都更有重量。真正的判斷力，會在這種時候被看見。": "节奏放慢、能见度压低，但也让每一步都更有重量。真正的判断力，会在这种时候被看见。",
            "CLEAR / 晴空": "CLEAR / 晴空",
            "01 / 04": "01 / 04",
            "世界神經圖 / Live World Pulse": "世界神经图 / Live World Pulse",
            "你做的一步，後面的世界會跟著一起動起來。": "你做的一步，后面的世界会跟著一起动起来。",
            "Interactive View": "Interactive View",
            "Formation": "Formation",
            "從第一隻夥伴開始，把自己的世界線一路養大": "从第一只伙伴开始，把自己的世界线一路养大",
            "先選夥伴，抽到第一批技能，再把戰鬥、導師、鍛裝、交易與六大地區一路推開。真正讓人停不下來的，不是功能有多少，而是這個世界會記住你怎麼玩，然後把後面的路越改越深。": "先选伙伴，抽到第一批技能，再把战斗、导师、锻装、交易与六大地区一路推开。真正让人停不下来的，不是功能有多少，而是这个世界会记住你怎么玩，然后把后面的路越改越深。",
            "前往 Renaiss": "前往 Renaiss",
            "回首頁": "回首页",
            "Renaiss World · Choose your future, raise your partner, and watch the world shift after every step.": "Renaiss World · Choose your future, raise your partner, and watch the world shift after every step.",
            "{ \"imports\": { \"three\": \"https://cdn.jsdelivr.net/npm/three@0.162.0/build/three.module.js\", \"three/addons/\": \"https://cdn.jsdelivr.net/npm/three@0.162.0/examples/jsm/\" } }": "{ \"imports\": { \"three\": \"https://cdn.jsdelivr.net/npm/three@0.162.0/build/three.module.js\", \"three/addons/\": \"https://cdn.jsdelivr.net/npm/three@0.162.0/examples/jsm/\" } }",
            "import { initGameNeuralStage } from \"./scripts/game-neural-stage.js\"; initGameNeuralStage();": "import { initGameNeuralStage } from \"./scripts/game-neural-stage.js\"; initGameNeuralStage();"
      },
      "en": {
            "Renaiss": "Renaiss",
            "Back": "Back",
            "世界觀": "Worldview",
            "介紹": "Introduction",
            "玩法": "How to play",
            "氣候": "Climate",
            "前往": "Go to",
            "官網": "Official website",
            "Choice-Driven Open World RPG": "Choice-Driven Open World RPG",
            "World": "World",
            "選擇你的": "Choose your",
            "未來": "Future",
            "帶著夥伴走進一個因你而改變的世界。": "Walk into a world changed because of you, with your partners.",
            "文字 RPG 遊戲": "Text RPG game",
            "立即看玩法": "Watch gameplay now",
            "先讀世界觀": "Read the world setting first",
            "向下滑，進入世界": "Swipe down, enter the world",
            "世界觀 / The World Behind The Routes": "Worldview / The World Behind The Routes",
            "你身在 Renaiss 海域。這片星域長年由 Renaiss 維運，是航道、交易與居住秩序的核心。": "You are in the Renaiss sea area. This star region has long been maintained by Renaiss, and is the core of shipping, trade, and residential order.",
            "World Lore": "World Lore",
            "但在明面秩序之外，另一股勢力正與既有體系長期角力。它們在各區節點滲透、造假、放出低價誘惑，試著把來源、鑑定與信任一點一點拆掉。": "However, outside the overt order, another force is long engaged in a protracted struggle with the existing system. They infiltrate nodes in each area, fabricate, and offer low-price temptations, attempting to dismantle source, authentication, and trust piece by piece.",
            "所以在": "Therefore in",
            "Renaiss World": "Renaiss World",
            "裡，你和夥伴不是只去探險。你是在調查來源、守住真偽、拆穿供應鏈裡的假象；每一次探索、交易、戰鬥、撤退，都會改寫下一段劇情。": "Here, you and your companions aren't just going on expeditions. You are investigating the source, guarding authenticity, and exposing the false appearances in the supply chain; each exploration, transaction, battle, and retreat will rewrite the next segment of the story.",
            "這是開放世界，沒有固定主線按鈕。章節、流言、戰況與角色命運都由你的選擇被動推進，最後變成所有玩家都看得見的長期傳聞。": "This is an open world with no fixed main quest button. Chapters, rumors, battle conditions, and character fates are passively driven by your choices, eventually becoming long‑term rumors that all players can see.",
            "Game Intro": "Game Intro",
            "遊戲介紹": "Game Introduction",
            "這是一個把選擇、夥伴、回合制戰鬥、鍛裝與交易一路串起來的文字 RPG。你不是在看世界運轉，而是在把自己的路一格一格打出來。": "This is a text RPG that weaves together choices, partners, turn‑based combat, equipment forging, and trading. You aren't watching the world spin; you're carving out your path step by step.",
            "從第一隻夥伴開始，慢慢養出自己的配招、戰線與傳聞": "Starting from your first partner, you'll gradually develop your own skill combos, battle lines, and rumors.",
            "你會先拿到夥伴和第一批技能，接著在回合制戰鬥裡磨出節奏，在導師與市場裡補齊關鍵招式，再把戰利品鍛成新裝，最後一路推進六大主地區。": "You'll first receive your partner and the first batch of skills, then hone your rhythm in turn‑based battles, supplement key moves with mentors and the market, forge loot into new gear, and finally push through the six major regions.",
            "世界分歧": "World divergence",
            "夥伴配招": "Partner skill setup",
            "回合制對戰": "Turn-based battle",
            "AI 鍛裝": "AI forging",
            "六地主線": "Six Realms Main Story",
            "Intro 01": "Intro 01",
            "選擇未來": "Choose the Future",
            "AI 劇情": "AI Storyline",
            "分歧路線": "Divergent Routes",
            "不是看劇情分支，是親手把下一章推向別的方向": "It's not about watching story branches; it's about personally pushing the next chapter in a different direction.",
            "調查、交涉、戰鬥、撤退，每個決定都會把後面的事件改寫。你怎麼出手，世界就怎麼回應。": "Investigation, negotiation, combat, retreat—each decision rewrites the events that follow. How you act, the world responds.",
            "你留下的痕跡，會回來找你：": "The traces you leave will come back to you:",
            "剛剛那一步，可能在下一段事件、下一場戰鬥，甚至更後面的局勢裡現身。": "That recent step might appear in the next event, the next battle, or even in later situations.",
            "同一場局面，可以走成不同命運：": "The same situation can lead to different fates:",
            "你可以硬闖、周旋、繞路或收手，世界回給你的後續也會完全不同。": "You can force through, negotiate, go around, or give up, and the world's response will be completely different.",
            "世界不是照劇本走，是照你留下的痕跡走": "The world doesn't follow a script; it follows the traces you leave.",
            "你做過的事不會消失，它只會在更後面的地方重新出現。": "What you have done won't disappear; it will only reappear further down the line.",
            "Intro 02": "Intro 02",
            "水火草起始": "Water, Fire, Grass Start",
            "技能晶片": "Skill Chip",
            "自由配招": "Free Skill Allocation",
            "寵物配技能，組出你的專屬配招": "Match your pet with skills, assemble your own custom moves.",
            "起點只有水、火、草三種，但真正的差別在後面。技能晶片一張張學進去之後，同一隻夥伴也能走成完全不同的戰法。": "The starting point only includes water, fire, and grass, but the real difference comes later. After learning skill chips one by one, the same partner can follow a completely different combat approach.",
            "起始屬性先決定開場手感：": "The initial attribute first determines the opening feel:",
            "水、火、草三種起步，會把你的前期節奏直接帶向不同方向。": "Starting with Water, Fire, or Grass will directly take your early-game rhythm in different directions.",
            "技能晶片會把同一隻夥伴養出不同個性：": "Skill chips will raise the same companion to develop different personalities:",
            "有人走爆發，有人走牽制，也有人把續戰和反打養成招牌。": "Some go for burst, some for control, and others make sustain and counterattack their signature.",
            "第一隻夥伴，就能長成你的代表作": "Your first companion can become your masterpiece.",
            "不是抽到別隻才有差，而是你怎麼養，牠就會怎麼打。": "It's not about pulling another one that makes the difference; it's how you raise it, and it will fight accordingly.",
            "Intro 03": "Intro 03",
            "回合制": "Turn-based",
            "速度定先手": "Speed determines who goes first",
            "屬性玩法": "Attribute gameplay",
            "回合制戰鬥裡，先手、屬性與技能配置會一起決定你的勝法": "In turn-based combat, the first move, attributes, and skill configuration together determine your victory method.",
            "這不是自動對轟。誰先出手、用哪個屬性切進去、五格技能怎麼排，會把每一場戰鬥拉成完全不同的節奏。": "This is not an auto clash. Who strikes first, which attribute you use to cut in, and how you arrange the five-slot skills will pull each battle into a completely different rhythm.",
            "速度決定先手：": "Speed determines the first move:",
            "先比招式速度，同速再比夥伴本身速度，真的一樣才會擲硬幣搶先手。": "First compare move speed, if tied then compare the partner's own speed, and if still tied, a coin flip determines who gets priority.",
            "屬性玩法：": "Attribute gameplay:",
            "水剋火、火剋草、草剋水；液態偏牽制與回補，熱能偏爆發與灼燒，生質偏綁定、護盾與續戰。": "Water beats Fire, Fire beats Grass, Grass beats Water; Liquids favor control and healing, thermal favors burst and burn, biomass favors binding, shields, and sustain.",
            "夥伴可裝備 5 個技能：": "Companion can equip 5 skills:",
            "起手、控場、反打、壓軸都由你自己選，T1 到 T3 的節奏也由你自己排。": "The opener, control, counterattack, and finisher are all up to you, and the rhythm from T1 to T3 is also up to you.",
            "技能獲取：": "Skill acquisition:",
            "開局免費五連抽會先送你第一批技能，導師戰贏了有機會直接傳招，玩家賣場則能讓你補齊想要的關鍵技能。": "The free 5-draw at the start will first give you the first batch of skills; winning a mentor battle gives a chance to directly learn a skill, while the player marketplace lets you fill in the key skills you want.",
            "真正上頭的地方，是你終於組出那套一出手就知道是你的配招": "The truly addictive part is when you finally assemble that set of combos that you can instantly recognize as your own.",
            "當速度、控制、爆發和保命咬在一起，你的打法才會真的成形。": "When speed, control, burst, and survivability mesh together, your playstyle will truly take shape.",
            "Intro 04": "Intro 04",
            "敵人戰": "Enemy Battle",
            "導師戰": "Mentor Battle",
            "好友戰": "Friend Battle",
            "敵人戰推主線，導師戰傳招，好友戰專打配招理解": "Enemy battles push the main storyline; mentor battles teach skills; friend battles focus on understanding skill combos.",
            "三種戰鬥，不是同一個介面換名字。你進的是不同戰線，拿回來的成長也完全不同。": "Three types of battles, not just the same interface with a different name. You enter different battle lines, and the growth you obtain is completely different.",
            "敵人戰：": "Enemy battle:",
            "把路打開，把資源帶回來，也把後面的風險和故事一起往前推。": "Open the road, bring back the resources, and also push forward the subsequent risks and stories together.",
            "導師戰：": "Mentor battle:",
            "把導師壓到指定血線就算通過考驗，贏下來還有機會把導師的招式學進自己隊伍。": "Push the mentor down to the designated health threshold to pass the trial, and winning gives you a chance to learn the mentor's moves into your own team.",
            "好友戰：": "Friend battle:",
            "不掉金幣、不上通緝、不碰生死，純粹比你的配招理解和對手到底誰更完整。": "No gold loss, no wanted level, no life‑and‑death; it's purely about whose deck‑building understanding and opponent's is more complete.",
            "同樣是打，拿回來的東西卻完全不同": "Even though it's the same type of fighting, what you bring back is completely different.",
            "有人拿資源，有人拿新招，有人拿到的是一場真正驗證自己構築的對局。": "Some obtain resources, some obtain new moves, and some obtain a match that truly validates their own build.",
            "Intro 05": "Intro 05",
            "裝備融合": "Equipment Fusion",
            "玩家賣場": "Player Marketplace",
            "資源流動": "Resource Flow",
            "三件藏品入爐，AI 會替你鍛出一件全新的裝備": "Three collectibles are placed into the furnace, AI will forge a brand-new equipment for you",
            "這裡的裝備不是固定掉落表。你丟進三件藏品，AI 會回你一件新裝，連名字、稀有度、價值與欄位都可能是第一次出現。": "Here the equipment is not a fixed drop table. You put three collectibles in, AI will return a new equipment, whose name, rarity, value, and slot may all be new.",
            "鍛裝有明確規則：": "The forging equipment has clear rules:",
            "只有藏品能入爐，技能晶片不會被拿去亂融。": "Only collectibles can be placed into the furnace; skill chips will not be used for random fusion.",
            "每次開鍛都像在等世界替你命名：": "Each time you start forging feels like waiting for the world to name you:",
            "AI 會重新組合名稱、稀有度、價值與欄位，不照固定配方出牌。": "AI will recombine names, rarity, value and fields, not following a fixed formula.",
            "賣場讓資源繼續流動：": "The marketplace keeps resources flowing:",
            "你用不到的戰利品和技能晶片，可以變成下一個人正缺的核心零件。": "The loot and skill chips you can't use can become the core parts the next person lacks.",
            "每次融合，都像在看這個世界會替你寫出什麼新名字": "Each fusion feels like watching the world write you a new name.",
            "戰利品不只會留在背包裡，它還可能變成你下一件主力。": "Loot doesn't just stay in your backpack; it might also become your next main weapon.",
            "Intro 06": "Intro 06",
            "六大地區": "Six major regions",
            "通緝壓力": "Wanted pressure",
            "Boss 戰線": "Boss front line",
            "六大主地區一路往深處打開，每一區都像新的主線入口": "The six main regions open up one after another into the depths, each area acting like a new mainline entry point.",
            "中原核心、西域沙海、南疆水網、北境高原、群島航線、隱秘深域，各有自己的勢力、節奏與壓力。你每進一區，世界就會再往深處打開一層。": "Central Plains Core, Western Desert Sea, Southern Frontier Water Network, Northern Plateau, Archipelago Routes, Hidden Deep Domain, each with its own forces, rhythm, and pressure. Every time you enter a region, the world opens another layer deeper.",
            "不是換背景，是換一套生存規則：": "It's not a change of background, but a change in the set of survival rules.",
            "每往前一步，節奏、敵人和代價都會變得更重。": "Every step forward, the rhythm, enemies, and cost become heavier.",
            "通緝、敵對勢力與 Boss 壓力會一路跟著你擴張：": "Wanted, hostile forces, and Boss pressure will follow you as it expands:",
            "你走到哪裡，戰線就長到哪裡。": "Wherever you go, the front line extends there.",
            "你以為自己只是在往前走，其實是在越走越深": "You think you're just moving forward, but you're actually going deeper.",
            "每推開一個地區，你拿到的不是下一張圖，而是下一段更重、更深的主線。": "Every time you push open a region, what you get is not the next image, but the next heavier, deeper main storyline.",
            "New Player Guide": "New Player Guide",
            "新手教學": "New Player Tutorial",
            "從 /start 到第一隻夥伴、第一套配招、第一場真正會讓你上頭的戰鬥，進場比你想的更快。": "From /start to the first partner, first ability set, and the first real battle that will get you hooked, getting started is faster than you think.",
            "先拿到夥伴和技能，再讓世界自己把你拖進去": "Get the partner and abilities first, then let the world pull you in on its own.",
            "語言、角色、夥伴、五連抽很快就會到手；剩下的樂趣，是你開始想下一套配招、下一場導師戰、下一個地區。": "Language, characters, companions, five-draw will be in hand soon; the remaining fun is you starting to think about the next set of combos, the next mentor battle, the next region.",
            "/start 開門": "/start open door",
            "錢包同步": "wallet sync",
            "夥伴誕生": "Companion's birth",
            "五連抽": "Five consecutive draws",
            "主線展開": "Main storyline unfolds",
            "Step 01": "Step 01",
            "Discord": "Discord",
            "/start": "/start",
            "立即開始": "Start immediately",
            "打一個 /start，你的世界線就會立刻打開": "Enter /start and your worldline will instantly open.",
            "在 Discord 輸入": "Enter in Discord.",
            "，系統就會立刻替你開出專屬討論串。不是先看一堆選單，而是直接讓你的冒險開始運轉。": "The system will instantly open a dedicated discussion thread for you. Instead of first browsing through a bunch of menus, it directly starts your adventure.",
            "不用找半天入口：": "No need to search for the entrance for a long time:",
            "指令一打，門就開了。": "As soon as you issue a command, the door opens.",
            "進去之後，世界會自己展開：": "After entering, the world will unfold on its own:",
            "角色、夥伴與後面的戰線，會依序在你面前打開。": "Roles, companions, and the frontlines behind them will open before you in order.",
            "先走進去，世界才會開始回應你": "Step inside first, and the world will start responding to you.",
            "這個遊戲最好的介紹，不在門外，而是在你按下 /start 之後。": "The best introduction to this game is not outside the door, but after you press /start.",
            "Step 02": "Step 02",
            "BSC 錢包": "BSC Wallet",
            "背景同步": "Background Sync",
            "可領 RNS": "Claimable RNS",
            "錢包先接上，資產與可領 RNS 會在背景裡慢慢補進來": "First connect the wallet; assets and claimable RNS will be added gradually in the background.",
            "這一步不是卡關，而是把鏈上資產接進你的世界。地址現在先填，角色建好後才正式綁定；同步完成後，可領 RNS 會自動入帳，你不用停下來等。": "This step is not a roadblock; it's about connecting on-chain assets to your world. Fill in the address now; the character will be officially bound after it is created. Once synchronization is complete, claimable RNS will be automatically credited, and you don't need to stop and wait.",
            "現在填先暫存，建角後才正式綁定：": "Now fill in the temporary storage; formal binding after character creation:",
            "不想現在處理也能先跳過，之後到設定再補。": "If you don't want to handle it now, you can also skip for now and add it later in settings.",
            "RNS 有明確換算規則：": "RNS has clear conversion rules:",
            "目前按開包與市場買入的總花費 × 0.5 計入可領 RNS。": "Currently, the total spending on opening packs and market purchases × 0.5 is counted toward claimable RNS.",
            "先接上，後面的經濟就會慢慢跟上你": "First connect, and the subsequent economy will slowly catch up with you.",
            "這不是把你卡在門口，而是先把鏈上資產接進你的冒險。": "This is not about keeping you stuck at the door, but about first connecting your on‑chain assets to your adventure.",
            "Step 03": "Step 03",
            "建立角色": "Create a character",
            "命名角色": "Name the character",
            "冒險入口": "Adventure Entrance",
            "給自己一個名字，讓世界開始記得你": "Give yourself a name, and the world will start remembering you.",
            "角色一旦命名，這個世界就不再把你當過客。故事會開始用你的名字開口，後面的選擇也會真的變成你的事。": "Once the character is named, the world will no longer treat you as a passerby. The story will begin speaking with your name, and the subsequent choices will truly become your own.",
            "從這一步開始，你不再是旁觀者：": "From this step onward, you are no longer a bystander:",
            "世界會把你算進它自己的秩序裡。": "The world will count you into its own order.",
            "你的名字會被帶進後面的事件裡：": "Your name will be brought into the events that follow:",
            "之後的路，會開始真正和你綁在一起。": "The road ahead will start to truly be bound to you.",
            "名字落下去的那一刻，你就不是旁觀者了": "The moment your name falls, you are no longer a bystander.",
            "從這一步開始，冒險不再發生在別人身上，而是發生在你身上。": "From this step onward, the adventure no longer happens to others, but to you.",
            "Step 04": "Step 04",
            "孵化寵物": "Hatch a pet",
            "夥伴同行": "Partner together",
            "選擇你的第一隻夥伴": "Choose your first companion",
            "水、火、草三種起始夥伴，決定的是你最初的節奏與氣質。再替牠取名，這隻夥伴就會陪你走進第一段故事、第一場戰鬥，還有後面的每一套配招。": "The three starter companions—Water, Fire, and Grass—determine your initial rhythm and temperament. Give them a name, and this companion will accompany you through the first story, the first battle, and every subsequent set of moves.",
            "起始屬性一變，開場手感就跟著變：": "If the starter type changes, the opening feel changes with it:",
            "你的第一套打法，從這一刻就已經決定一半。": "Your first set of tactics is already half decided from this moment.",
            "第一隻夥伴不是過場：": "The first companion is not a cutscene:",
            "它會陪你把第一套戰法從雛形養成真正的主力。": "It will accompany you as you develop the first set of battle tactics from a nascent form into a true main force.",
            "很多人愛上這個世界，就是從第一隻夥伴開始": "Many people fall in love with this world, starting with the first companion.",
            "當你替牠取完名字，這場冒險通常就真的開始有感覺了。": "When you give it a name, this adventure usually really starts to feel right.",
            "Step 05": "Step 05",
            "免費五連抽": "Free five-pull",
            "配招成形": "Skill Build Formation",
            "五連抽一開，第一套能改變打法的技能就會落進你手裡": "When the five-draw starts, the first skill set that can change your tactics will land in your hands.",
            "夥伴孵化完成後，系統會直接送上免費五連抽。晶片會留在背包裡，等你學進夥伴、掛上賣場，或替下一套配招先埋伏筆。": "After partner hatching is complete, the system will directly grant a free five-draw. The chip will remain in your inventory, waiting for you to equip it onto your partner, list it on the marketplace, or use it as a foreshadow for the next skill build.",
            "開場就有技能能玩：": "At the start, there are skills you can play:",
            "你不用等很久，第一套配招很快就會開始成形。": "You don't have to wait long, the first combo will quickly start forming.",
            "晶片是真的資產，不是一閃而過的演出：": "Chips are real assets, not a fleeting show:",
            "它會留在你手上，等你拿去學、拿去賣，或等下一隻夥伴來用。": "It will stay in your hand, waiting for you to take it to learn, to sell, or wait for the next companion to use.",
            "第一批技能一到手，你就會開始想下一套配招": "Once you get the first batch of skills, you'll start thinking about the next set of combos.",
            "這不是暖身，它就是你第一批真正能改變打法的戰力。": "This is not a warm-up; it's the first real combat power that can change your playstyle.",
            "Step 06": "Step 06",
            "主選單": "Main Menu",
            "玩法展開": "Expand Gameplay",
            "一路解鎖": "Unlock as you go",
            "主選單一開，整個世界才正式展開": "When the main menu opens, the entire world officially unfolds.",
            "故事、地圖、戰鬥、背包、融合、賣場、導師切磋與好友戰，會隨著你的進度一層層展開。你不用一次學完，只要先讓自己走進去。": "Story, map, combat, inventory, fusion, shop, mentor sparring, and friend battles will unfold layer by layer as you progress. You don't need to learn everything at once; just step in first.",
            "規則不會一次塞滿：": "Rules will not be crammed all at once:",
            "你先往前走，該出現的玩法會在對的時候出現。": "Go ahead first; the appropriate gameplay will appear at the right time.",
            "深度會追著你長出來：": "Depth will follow you as it grows:",
            "你每往前玩一步，這個世界就會再多一層可以碰的東西。": "Each step you take forward in the game adds another layer of interactable things to the world.",
            "真正讓人停不下來的，是世界會越玩越大": "What truly makes it impossible to stop is that the world keeps growing the more you play.",
            "你每往前走一步，新的玩法和新的壓力就會自己長出來。": "Each step you take forward, new gameplay and new pressure emerge on their own.",
            "Climate States": "Climate States",
            "動態氣候 / Dynamic Climate": "Dynamic Climate",
            "這不是背景換色，而是同一個世界在四種氣候裡露出四種節奏。晴空讓你推進，降雨帶來變數，旱象逼你精算，降雪把每一步都壓得更重。": "This is not a background color change, but the same world showing four rhythms in four climates. Clear skies let you advance, rain brings variables, drought forces you to calculate precisely, and snow makes each step heavier.",
            "晴空 / Clear Sky · 推進期": "Clear Sky · Push Phase",
            "降雨 / Rainfall · 變數期": "Rainfall · Variable Phase",
            "光線、路面與事件節奏都開始變動，適合快推、快收、快離場，每一步都更講究判斷。": "Light, road conditions, and event timing all begin to shift, suitable for quick push, quick collect, and quick exit; each step demands sharper judgment.",
            "旱象 / Drought · 緊縮期": "Drought · Contraction Phase",
            "補給與撤退都變得尖銳，錯一步就會被放大。這種氣候會逼你把每個選擇算得更狠。": "Both resupply and retreat become razor‑sharp; a single misstep gets amplified. This atmosphere forces you to calculate every choice more ruthlessly.",
            "降雪 / Snowfall · 試煉期": "Snowfall / Snowfall · Trial Period",
            "節奏放慢、能見度壓低，但也讓每一步都更有重量。真正的判斷力，會在這種時候被看見。": "The tempo slows, visibility drops, but it also makes each step carry more weight. True judgment is revealed at such times.",
            "01 / 04": "01 / 04",
            "世界神經圖 / Live World Pulse": "World Neural Map / Live World Pulse",
            "你做的一步，後面的世界會跟著一起動起來。": "The step you take will cause the world behind to start moving together.",
            "Interactive View": "Interactive View",
            "Formation": "Formation",
            "從第一隻夥伴開始，把自己的世界線一路養大": "Starting from the first companion, grow your own worldline all the way.",
            "先選夥伴，抽到第一批技能，再把戰鬥、導師、鍛裝、交易與六大地區一路推開。真正讓人停不下來的，不是功能有多少，而是這個世界會記住你怎麼玩，然後把後面的路越改越深。": "First select a companion, draw the first batch of skills, then unlock battle, mentor, forging, trading, and the six major regions along the way. What truly makes it hard to stop is not how many features there are, but that this world will remember how you play, and then the later paths become deeper and deeper.",
            "前往 Renaiss": "Go to Renaiss",
            "回首頁": "Back to home",
            "Renaiss World · Choose your future, raise your partner, and watch the world shift after every step.": "Renaiss World · Choose your future, raise your partner, and watch the world shift after every step.",
            "同一條路，氣候一變，打法就跟著變。": "Same road, different climate, different way to play.",
            "視野乾淨，節奏平穩，適合推主線、探圖、整理資源，像替下一段冒險先鋪好路。": "Clean visibility and stable pacing make this the best state for pushing the main route, scouting, and preparing resources for the next stretch.",
            "CLEAR / 晴空": "CLEAR / Clear Sky"
      },
      "ko": {
            "Renaiss": "Renaiss",
            "Back": "뒤로",
            "世界觀": "세계관",
            "介紹": "소개",
            "玩法": "게임 방법",
            "氣候": "기후",
            "前往": "이동",
            "官網": "공식 웹사이트",
            "Choice-Driven Open World RPG": "선택 기반 오픈 월드 RPG",
            "World": "세계",
            "選擇你的": "당신의 선택",
            "未來": "미래",
            "帶著夥伴走進一個因你而改變的世界。": "파트너와 함께 당신이 변화시킨 세계에 들어갑니다。",
            "文字 RPG 遊戲": "텍스트 RPG 게임",
            "立即看玩法": "지금 바로 플레이 방법 보기",
            "先讀世界觀": "먼저 세계관 읽기",
            "向下滑，進入世界": "아래로 밀면 세계에 진입",
            "世界觀 / The World Behind The Routes": "세계관 / The World Behind The Routes",
            "你身在 Renaiss 海域。這片星域長年由 Renaiss 維運，是航道、交易與居住秩序的核心。": "당신은 Renaiss 해역에 있습니다. 이 별 영역은 평상시에 Renaiss가 운영하며, 항로, 거래와 거주 질서의 핵심입니다.",
            "World Lore": "세계관",
            "但在明面秩序之外，另一股勢力正與既有體系長期角力。它們在各區節點滲透、造假、放出低價誘惑，試著把來源、鑑定與信任一點一點拆掉。": "그러나 표면 질서 밖에서, 다른 세력이 기존의 체계와 장기적으로 대치하고 있다. 그들은 각 지역의 노드에 침투하고, 위조하며, 낮은 가격의 유혹을 던지며, 출처, 감정 및 신뢰를 조금씩 무너뜨린다.",
            "所以在": "그래서 ",
            "Renaiss World": "Renaiss World",
            "裡，你和夥伴不是只去探險。你是在調查來源、守住真偽、拆穿供應鏈裡的假象；每一次探索、交易、戰鬥、撤退，都會改寫下一段劇情。": "여기서, 당신과 동료들은 단순히 탐험하러 가는 것이 아닙니다. 출처를 조사하고, 진위를 지키며, 공급망 속의 거짓을 폭로합니다; 모든 탐험, 거래, 전투, 후퇴는 다음 이야기를 다시 쓸 것입니다.",
            "這是開放世界，沒有固定主線按鈕。章節、流言、戰況與角色命運都由你的選擇被動推進，最後變成所有玩家都看得見的長期傳聞。": "이것은 오픈월드이며, 고정된 메인 퀘스트 버튼이 없습니다. 챕터, 소문, 전투 상황과 캐릭터의 운명은 당신의 선택에 의해 수동적으로 진행되며, 결국 모든 플레이어가 볼 수 있는 장기적 전설이 됩니다.",
            "Game Intro": "게임 소개",
            "遊戲介紹": "게임 소개",
            "這是一個把選擇、夥伴、回合制戰鬥、鍛裝與交易一路串起來的文字 RPG。你不是在看世界運轉，而是在把自己的路一格一格打出來。": "이것은 선택, 파트너, 턴제 전투, 장비 제작과 거래를 하나의 흐름으로 연결한 텍스트 RPG입니다. 당신은 세계가 돌아가는 것을 바라보는 것이 아니라, 자신의 길을 한 칸 한 칸 만들어 나가는 것입니다.",
            "從第一隻夥伴開始，慢慢養出自己的配招、戰線與傳聞": "첫 번째 파트너부터 시작하여, 천천히 자신만의 스킬 조합, 전투 라인, 그리고 소문을 만들어 갑니다.",
            "你會先拿到夥伴和第一批技能，接著在回合制戰鬥裡磨出節奏，在導師與市場裡補齊關鍵招式，再把戰利品鍛成新裝，最後一路推進六大主地區。": "먼저 파트너와 첫 번째 스킬을 받고, 이어서 턴제 전투에서 리듬을 잡은 후, 멘토와 시장에서 핵심 스킬을 보완하고, 전리품을 새 장비로 단련한 뒤, 마지막으로 여섯 개의 주요 지역을 밀고 나간다.",
            "世界分歧": "세계 분기",
            "夥伴配招": "파트너 스킬 조합",
            "回合制對戰": "턴제 전투",
            "AI 鍛裝": "AI 장비 단조",
            "六地主線": "6지역 본선",
            "Intro 01": "Intro 01",
            "選擇未來": "미래를 선택",
            "AI 劇情": "AI 드라마",
            "分歧路線": "분기 노선",
            "不是看劇情分支，是親手把下一章推向別的方向": "시나리오 분기를 보는 것이 아니라, 직접 다음 챕터를 다른 방향으로 밀어붙이는 것이다.",
            "調查、交涉、戰鬥、撤退，每個決定都會把後面的事件改寫。你怎麼出手，世界就怎麼回應。": "조사, 교섭, 전투, 후퇴 — 모든 결정이 뒤에 올 일을 바꿔 쓴다. 당신이 어떻게 행동하느냐에 따라 세계가 어떻게 응답한다.",
            "你留下的痕跡，會回來找你：": "당신이 남긴 흔적은 다시 당신을 찾아옵니다：",
            "剛剛那一步，可能在下一段事件、下一場戰鬥，甚至更後面的局勢裡現身。": "방금 그 한 발짝은 다음 사건, 다음 전투, 심지어 그 이후의 상황에서도 나타날 수 있습니다.",
            "同一場局面，可以走成不同命運：": "같은 상황은 다른 운명으로 전개될 수 있습니다：",
            "你可以硬闖、周旋、繞路或收手，世界回給你的後續也會完全不同。": "당신은 강행하거나, 협상하거나, 우회하거나, 포기가 가능하며, 세계가 당신에게 되돌려주는 후속은 완전히 달라질 것입니다.",
            "世界不是照劇本走，是照你留下的痕跡走": "세상은 대본대로 움직이지 않고, 당신이 남긴 흔적대로 움직인다.",
            "你做過的事不會消失，它只會在更後面的地方重新出現。": "당신이 한 일은 사라지지 않으며, 그것은 더 나중에 다시 나타날 뿐이다.",
            "Intro 02": "인트로 02",
            "水火草起始": "물불풀 시작",
            "技能晶片": "스킬 칩",
            "自由配招": "자유 스킬 조합",
            "寵物配技能，組出你的專屬配招": "펫 스킬 조합으로 나만의 전용 스킬 조합을 만들어 보세요.",
            "起點只有水、火、草三種，但真正的差別在後面。技能晶片一張張學進去之後，同一隻夥伴也能走成完全不同的戰法。": "시작은 물, 불, 풀 세 가지뿐이지만, 진정한 차이는 뒤에 온다. 스킬 칩을 하나씩 배우면, 같은 동료도 완전히 다른 전략으로 발전할 수 있다.",
            "起始屬性先決定開場手感：": "시작 속성이 먼저 시작 감각을 결정합니다：",
            "水、火、草三種起步，會把你的前期節奏直接帶向不同方向。": "물, 불, 풀 세 가지 시작이 초기 리듬을 서로 다른 방향으로 이끕니다。",
            "技能晶片會把同一隻夥伴養出不同個性：": "스킬 칩은 같은 파트너에게 다른 개성을 부여합니다：",
            "有人走爆發，有人走牽制，也有人把續戰和反打養成招牌。": "일부 사람은 폭발적인 플레이를 하고, 일부는 견제하며, 또 일부는 지속전과 역공을 자신만의 특징으로 삼는다.",
            "第一隻夥伴，就能長成你的代表作": "첫 번째 파트너만으로도 당신의 대표작이 될 수 있다.",
            "不是抽到別隻才有差，而是你怎麼養，牠就會怎麼打。": "다른 캐릭터를 뽑는 것의 차이가 아니라, 당신이 어떻게 키우느냐에 따라 그들이 어떻게 싸우느냐가 결정된다.",
            "Intro 03": "인트로 03",
            "回合制": "턴제",
            "速度定先手": "속도 결정 선공",
            "屬性玩法": "속성 플레이",
            "回合制戰鬥裡，先手、屬性與技能配置會一起決定你的勝法": "턴제 전투에서 선공, 속성, 스킬 배치가 승패를 결정합니다",
            "這不是自動對轟。誰先出手、用哪個屬性切進去、五格技能怎麼排，會把每一場戰鬥拉成完全不同的節奏。": "이건 자동 대결이 아닙니다. 누가 먼저 공격하고, 어떤 속성으로 진입하며, 5칸 스킬을 어떻게 배치하느냐에 따라 매 전투의 리듬이 완전히 달라집니다.",
            "速度決定先手：": "속도가 선공을 결정합니다:",
            "先比招式速度，同速再比夥伴本身速度，真的一樣才會擲硬幣搶先手。": "먼저 기술의 속도를 비교하고, 동일할 경우 파트너 자체 속도를 비교하며, 그래도 같으면 동전 던지기로 선공을 정합니다.",
            "屬性玩法：": "속성 플레이 방식:",
            "水剋火、火剋草、草剋水；液態偏牽制與回補，熱能偏爆發與灼燒，生質偏綁定、護盾與續戰。": "물은 불을 이기고, 불은 풀을 이기며, 풀은 물을 이긴다; 액체는 견제와 보강에 치중하고, 열은 폭발과 화상에 치중하며, 생체는 결합, 방패와 지속전에 치중한다.",
            "夥伴可裝備 5 個技能：": "파트너는 5개의 스킬을 장착할 수 있다:",
            "起手、控場、反打、壓軸都由你自己選，T1 到 T3 的節奏也由你自己排。": "오프닝, 장악, 반격, 피날레는 모두 직접 선택하고, T1부터 T3까지의 리듬도 직접 배치한다.",
            "技能獲取：": "스킬 획득：",
            "開局免費五連抽會先送你第一批技能，導師戰贏了有機會直接傳招，玩家賣場則能讓你補齊想要的關鍵技能。": "초반 무료 5연 뽑기가 먼저 첫 번째 스킬을 줍니다, 멘토전에서 이기면 직접 스킬을 전수받을 기회가 있습니다, 플레이어 마켓에서 원하는 핵심 스킬을 보완할 수 있습니다.",
            "真正上頭的地方，是你終於組出那套一出手就知道是你的配招": "정말 중독되는 부분은 당신이 마침내 한 번에 누군가의 것인 줄 알 정도로 자신의 스킬 조합을 완성했을 때입니다.",
            "當速度、控制、爆發和保命咬在一起，你的打法才會真的成形。": "속도, 제어, 폭발, 그리고 생존의 물기가 함께 어우러질 때, 당신의 플레이가 비로소 완성된다.",
            "Intro 04": "Intro 04",
            "敵人戰": "적 전투",
            "導師戰": "멘토전",
            "好友戰": "친구전",
            "敵人戰推主線，導師戰傳招，好友戰專打配招理解": "적전투는 메인 라인을 밀고，멘토전은 스킬을 전달하며，친구전은 조합 이해에 집중한다.",
            "三種戰鬥，不是同一個介面換名字。你進的是不同戰線，拿回來的成長也完全不同。": "세 가지 전투는 같은 인터페이스에서 이름을 바꾼 것이 아니다. 당신이 들어간 것은 다른 전투선이며, 가져오는 성장도 완전히 다르다.",
            "敵人戰：": "적 전투：",
            "把路打開，把資源帶回來，也把後面的風險和故事一起往前推。": "길을 열고, 자원을 가져오며, 뒤에 있는 위험과 이야기까지 함께 앞으로 밀어낸다.",
            "導師戰：": "멘토 전투：",
            "把導師壓到指定血線就算通過考驗，贏下來還有機會把導師的招式學進自己隊伍。": "멘토를 지정된 체력선까지 누르면 테스트를 통과하고, 이기면 멘토의 기술을 내 팀에 배울 기회도 있다.",
            "好友戰：": "친구전:",
            "不掉金幣、不上通緝、不碰生死，純粹比你的配招理解和對手到底誰更完整。": "골드를 잃지 않고, 체포되지 않으며, 생사에 닿지 않으며, 순수하게 당신의 포켓몬 스킬 배치 이해와 상대가 누구 더 완전한지를 비교한다.",
            "同樣是打，拿回來的東西卻完全不同": "같은 타격인데, 가져오는 것이 완전히 다르다",
            "有人拿資源，有人拿新招，有人拿到的是一場真正驗證自己構築的對局。": "누군가는 자원을 가져가고, 누군가는 새로운 기술을 가져가며, 누군가는 자신의 구축을 진정으로 검증하는 대국을 가져간다.",
            "Intro 05": "Intro 05",
            "裝備融合": "장비 융합",
            "玩家賣場": "플레이어 마켓",
            "資源流動": "자원 흐름",
            "三件藏品入爐，AI 會替你鍛出一件全新的裝備": "세 개의 수집품이 용광로에 들어가고, AI가 당신을 위해 완전히 새로운 장비를 단조합니다.",
            "這裡的裝備不是固定掉落表。你丟進三件藏品，AI 會回你一件新裝，連名字、稀有度、價值與欄位都可能是第一次出現。": "여기서의 장비는 고정 드롭 테이블이 아닙니다. 당신이 세 개의 수집품을 넣으면 AI가 새로운 장비를 돌려주는데, 이름, 희귀도, 가치, 슬롯이 처음 나타날 수도 있습니다.",
            "鍛裝有明確規則：": "장비 단조에는 명확한 규칙이 있습니다:",
            "只有藏品能入爐，技能晶片不會被拿去亂融。": "컬렉션만 용광로에 넣을 수 있으며, 스킬 칩은 함부로 합성되지 않습니다.",
            "每次開鍛都像在等世界替你命名：": "매번 단조를 열 때마다 세상을 기다리듯 네 이름을 지어주는 느낌이 든다:",
            "AI 會重新組合名稱、稀有度、價值與欄位，不照固定配方出牌。": "AI는 이름, 희귀도, 가치 및 필드를 재구성하여 고정된 조합에 따라 카드를 뽑지 않는다.",
            "賣場讓資源繼續流動：": "마켓에서 자원이 계속 흐르도록 합니다:",
            "你用不到的戰利品和技能晶片，可以變成下一個人正缺的核心零件。": "사용하지 않는 전리품과 스킬 칩은 다음 사람이 필요로 하는 핵심 부품이 될 수 있습니다.",
            "每次融合，都像在看這個世界會替你寫出什麼新名字": "매번 융합할 때마다, 이 세상이 당신을 위해 어떤 새 이름을 써줄지 보는 것 같습니다.",
            "戰利品不只會留在背包裡，它還可能變成你下一件主力。": "전리품은 배낭에만 남아있는 것이 아니라, 다음 주력 무기가 될 수도 있습니다.",
            "Intro 06": "인트로 06",
            "六大地區": "6대 지역",
            "通緝壓力": "수배 압력",
            "Boss 戰線": "Boss 전선",
            "六大主地區一路往深處打開，每一區都像新的主線入口": "6대 주요 지역이 한결같이 깊이 열려가며, 각 지역은 새로운 메인라인 입구처럼 보인다.",
            "中原核心、西域沙海、南疆水網、北境高原、群島航線、隱秘深域，各有自己的勢力、節奏與壓力。你每進一區，世界就會再往深處打開一層。": "中原核心,西域沙海,南疆水網,北境高原,群島航線,隱秘深域은 각각 자신만의 세력, 리듬, 압력을 가지고 있다. 당신이 한 구역에 들어설 때마다 세계는 한 층 더 깊은 곳으로 열리게 된다.",
            "不是換背景，是換一套生存規則：": "배경을 바꾸는 것이 아니라 생존 규칙을 바꾸는 것이다:",
            "每往前一步，節奏、敵人和代價都會變得更重。": "한 발자국 더 나아갈 때마다 리듬, 적, 대가가 더 무거워진다.",
            "通緝、敵對勢力與 Boss 壓力會一路跟著你擴張：": "수배, 적대 세력 및 보스 압력이 당신의 확장과 함께 따라옵니다：",
            "你走到哪裡，戰線就長到哪裡。": "당신이 가는 곳마다 전선이 그곳까지 늘어난다.",
            "你以為自己只是在往前走，其實是在越走越深": "당신은 그냥 앞으로 나아가고 있다고 생각하지만, 사실은 점점 더 깊어지고 있다.",
            "每推開一個地區，你拿到的不是下一張圖，而是下一段更重、更深的主線。": "모든 지역을 열 때마다, 당신이 받는 것은 다음 그림이 아니라 더 무겁고 더 깊은 메인 스토리라인입니다.",
            "New Player Guide": "새로운 플레이어 가이드",
            "新手教學": "초보자 튜토리얼",
            "從 /start 到第一隻夥伴、第一套配招、第一場真正會讓你上頭的戰鬥，進場比你想的更快。": "시작(/start)에서 첫 번째 파트너, 첫 번째 스킬 조합, 그리고 당신을 정말로 열광하게 만드는 첫 번째 전투까지, 입장이 생각보다 빠르다.",
            "先拿到夥伴和技能，再讓世界自己把你拖進去": "먼저 파트너와 스킬을 확보한 후, 세계가 스스로 당신을 끌어들인다.",
            "語言、角色、夥伴、五連抽很快就會到手；剩下的樂趣，是你開始想下一套配招、下一場導師戰、下一個地區。": "언어, 캐릭터, 파트너, 5연속 뽑기가 곧 손에 들어온다; 남은 재미는 다음 스킬 조합, 다음 멘토전, 다음 지역을 생각하기 시작할 때이다.",
            "/start 開門": "/start 문 열다",
            "錢包同步": "지갑 동기화",
            "夥伴誕生": "동료 탄생",
            "五連抽": "5연 뽑기",
            "主線展開": "메인 전개",
            "Step 01": "Step 01",
            "Discord": "Discord",
            "/start": "/start",
            "立即開始": "즉시 시작",
            "打一個 /start，你的世界線就會立刻打開": "/start을 입력하면 당신의 세계선이 즉시 열립니다",
            "在 Discord 輸入": "Discord에서 입력",
            "，系統就會立刻替你開出專屬討論串。不是先看一堆選單，而是直接讓你的冒險開始運轉。": "시스템이 즉시 당신을 위해 전용 토론 스레드를 열어줍니다. 여러 메뉴를 먼저 보는 것이 아니라, 바로 당신의 모험이 작동하기 시작합니다.",
            "不用找半天入口：": "입구를 찾을 필요가 없습니다:",
            "指令一打，門就開了。": "명령을 입력하면 문이 열립니다.",
            "進去之後，世界會自己展開：": "들어간 후 세상이 저절로 펼쳐집니다:",
            "角色、夥伴與後面的戰線，會依序在你面前打開。": "캐릭터, 파트너, 그리고 뒤의 전투선은 순서대로 당신 앞에 펼쳐진다.",
            "先走進去，世界才會開始回應你": "먼저 들어가면, 세계가 당신에게 응답하기 시작한다.",
            "這個遊戲最好的介紹，不在門外，而是在你按下 /start 之後。": "이 게임의 가장 좋은 소개는 문 밖이 아니라, 당신이 /start를 누른 후에 있다.",
            "Step 02": "02단계",
            "BSC 錢包": "BSC 지갑",
            "背景同步": "백그라운드 동기화",
            "可領 RNS": "RNS 수령 가능",
            "錢包先接上，資產與可領 RNS 會在背景裡慢慢補進來": "지갑을 먼저 연결하세요, 자산과 받을 수 있는 RNS가 백그라운드에서 천천히 추가될 것입니다.",
            "這一步不是卡關，而是把鏈上資產接進你的世界。地址現在先填，角色建好後才正式綁定；同步完成後，可領 RNS 會自動入帳，你不用停下來等。": "이 단계는 막힌 것이 아닙니다, 그러나 체인 위의 자산을 당신의 세계에 연결하는 것입니다. 지금은 주소를 먼저 입력하세요, 캐릭터가 만들어진 후에야 비로소 정식으로 연결됩니다; 동기화가 완료된 후, 받을 수 있는 RNS가 자동으로 입금되며, 멈출 필요가 없습니다.",
            "現在填先暫存，建角後才正式綁定：": "지금은 임시로 저장하고, 계정을 만든 후 정식 연결：",
            "不想現在處理也能先跳過，之後到設定再補。": "지금은 처리하고 싶지 않으면 건너뛰고, 나중에 설정에서 채울 수 있습니다。",
            "RNS 有明確換算規則：": "RNS에는 명확한 환산 규칙이 있다：",
            "目前按開包與市場買入的總花費 × 0.5 計入可領 RNS。": "현재 개봉과 시장에서 구매한 총 비용 × 0.5가 청구 가능한 RNS에 반영됩니다.",
            "先接上，後面的經濟就會慢慢跟上你": "먼저 연결하면, 이후 경제가 점점 따라올 것입니다.",
            "這不是把你卡在門口，而是先把鏈上資產接進你的冒險。": "이것은 당신을 입구에서 가두는 것이 아니라, 먼저 체인상의 자산을 당신의 모험에 연결하는 것입니다.",
            "Step 03": "Step 03",
            "建立角色": "캐릭터 생성",
            "命名角色": "캐릭터 이름 지정",
            "冒險入口": "모험 입구",
            "給自己一個名字，讓世界開始記得你": "자기에게 이름을 부여하고, 세상이 당신을 기억하기 시작하도록 하세요.",
            "角色一旦命名，這個世界就不再把你當過客。故事會開始用你的名字開口，後面的選擇也會真的變成你的事。": "캐릭터가 한 번 이름이 붙으면, 이 세계는 당신을 더 이상 지나가는 손님으로 보지 않습니다. 이야기는 당신의 이름으로 말하기 시작하고, 이후의 선택도 진정으로 당신의 것이 됩니다.",
            "從這一步開始，你不再是旁觀者：": "이 순간부터, 당신은 더 이상 방관자가 아닙니다:",
            "世界會把你算進它自己的秩序裡。": "세상은 당신을 자신의 질서에 포함시킬 것입니다.",
            "你的名字會被帶進後面的事件裡：": "당신의 이름은 뒤따르는 사건에 포함될 것입니다:",
            "之後的路，會開始真正和你綁在一起。": "이후의 길은 이제 진정으로 너와 얽히게 될 것이다.",
            "名字落下去的那一刻，你就不是旁觀者了": "이름이 적힌 순간, 너는 더 이상 관전자가 아니다.",
            "從這一步開始，冒險不再發生在別人身上，而是發生在你身上。": "이 단계부터 모험은 더 이상 다른 사람에게 일어나지 않고, 당신에게 일어납니다.",
            "Step 04": "Step 04",
            "孵化寵物": "펫 부화",
            "夥伴同行": "파트너와 함께",
            "選擇你的第一隻夥伴": "첫 번째 파트너를 선택하세요",
            "水、火、草三種起始夥伴，決定的是你最初的節奏與氣質。再替牠取名，這隻夥伴就會陪你走進第一段故事、第一場戰鬥，還有後面的每一套配招。": "물, 불, 풀 세 가지 시작 파트너, 결정하는 것은 당신의 초기 리듬과 기질입니다. 이름을 붙이면 이 파트너는 당신과 함께 첫 번째 이야기, 첫 번째 전투, 그리고 그 이후의 모든 스킬 조합에 동행하게 됩니다.",
            "起始屬性一變，開場手感就跟著變：": "시작 속성이 바뀌면, 오프닝 감각도 따라 바뀝니다:",
            "你的第一套打法，從這一刻就已經決定一半。": "당신의 첫 번째 전법은 이 순간부터 이미 절반이 결정됩니다.",
            "第一隻夥伴不是過場：": "첫 번째 파트너는 단순한 지나가는 존재가 아닙니다:",
            "它會陪你把第一套戰法從雛形養成真正的主力。": "그것은 당신이 첫 번째 전투법을 초안에서 진정한 주력으로 발전시키는 동안 함께해 줄 것입니다.",
            "很多人愛上這個世界，就是從第一隻夥伴開始": "많은 사람들이 첫 번째 동료부터 이 세계에 빠지게 됩니다.",
            "當你替牠取完名字，這場冒險通常就真的開始有感覺了。": "이름을 붙여주면 이 모험은 대개 진짜로 시작된 느낌이 들기 시작합니다.",
            "Step 05": "Step 05",
            "免費五連抽": "무료 5연속 뽑기",
            "配招成形": "스킬 조합 형성",
            "五連抽一開，第一套能改變打法的技能就會落進你手裡": "5연이 시작되면, 플레이 방식을 바꿀 수 있는 첫 번째 스킬이 바로 손에 들어옵니다.",
            "夥伴孵化完成後，系統會直接送上免費五連抽。晶片會留在背包裡，等你學進夥伴、掛上賣場，或替下一套配招先埋伏筆。": "파트너가 부화 완료되면 시스템이 즉시 무료 5연을 제공합니다. 칩은 가방에 남아 있으며, 파트너에게 배우거나 판매장에 등록하거나, 다음 세트 콤비네이션을 위해 선행으로 배치할 때까지 기다립니다.",
            "開場就有技能能玩：": "시작부터 스킬을 사용할 수 있습니다:",
            "你不用等很久，第一套配招很快就會開始成形。": "당신은 오래 기다릴 필요 없어요, 첫 번째 스킬 세트가 곧 형성되기 시작할 거예요.",
            "晶片是真的資產，不是一閃而過的演出：": "칩은 진짜 자산이며, 순간적인 쇼가 아닙니다:",
            "它會留在你手上，等你拿去學、拿去賣，或等下一隻夥伴來用。": "이것은 당신의 손에 남아 있을 것이며, 당신이 배우거나 팔거나, 또는 다음 파트너가 사용할 때까지 기다립니다.",
            "第一批技能一到手，你就會開始想下一套配招": "첫 번째 스킬 세트를 手에 넣는 순간, 당신은 바로 다음 스킬 조합에 대해 생각하기 시작한다.",
            "這不是暖身，它就是你第一批真正能改變打法的戰力。": "이건 워밍업이 아니라, 당신의 플레이 방식을 실제로 바꿀 수 있는 첫 번째 전투력이다.",
            "Step 06": "Step 06",
            "主選單": "메인 메뉴",
            "玩法展開": "게임 방법",
            "一路解鎖": "한 번에 잠금 해제",
            "主選單一開，整個世界才正式展開": "메인 메뉴가 열리면, 세상이 비로소 본격적으로 펼쳐진다.",
            "故事、地圖、戰鬥、背包、融合、賣場、導師切磋與好友戰，會隨著你的進度一層層展開。你不用一次學完，只要先讓自己走進去。": "스토리, 맵, 전투, 가방, 합성, 상점, 멘토 대결과 친구 전투가 당신의 진행 상황에 따라 한층씩 펼쳐진다. 한 번에 다 배울 필요 없이, 먼저 자신이 그 세계에 발을 들이면 된다.",
            "規則不會一次塞滿：": "규칙이 한 번에 가득 채워지지 않는다:",
            "你先往前走，該出現的玩法會在對的時候出現。": "먼저 앞으로 나아가세요, 나타날 놀이법은 정확한 순간에 나타날 거예요.",
            "深度會追著你長出來：": "깊이가 당신을 따라 자라납니다:",
            "你每往前玩一步，這個世界就會再多一層可以碰的東西。": "매번 앞으로 한 걸음 플레이할 때마다, 이 세계는 당신이 만질 수 있는 또 다른 층을 더하게 됩니다.",
            "真正讓人停不下來的，是世界會越玩越大": "정말로 멈출 수 없게 만드는 건 세계가 점점 더 커진다는 것이다.",
            "你每往前走一步，新的玩法和新的壓力就會自己長出來。": "당신이 한 걸음씩 앞으로 나아갈 때마다 새로운 플레이 방식과 새로운 압력이 저절로 생겨난다.",
            "Climate States": "기후 상태",
            "動態氣候 / Dynamic Climate": "동적 기후",
            "CLEAR / 晴空": "CLEAR / 맑음",
            "01 / 04": "01 / 04",
            "世界神經圖 / Live World Pulse": "세계 신경도 / Live World Pulse",
            "你做的一步，後面的世界會跟著一起動起來。": "당신이 내딛는 한 걸음이 뒤에 있는 세계도 함께 움직이기 시작합니다.",
            "Interactive View": "대화형 보기",
            "Formation": "형성",
            "從第一隻夥伴開始，把自己的世界線一路養大": "첫 번째 파트너부터 시작하여 자신의 세계선을 끝까지 키워나간다",
            "先選夥伴，抽到第一批技能，再把戰鬥、導師、鍛裝、交易與六大地區一路推開。真正讓人停不下來的，不是功能有多少，而是這個世界會記住你怎麼玩，然後把後面的路越改越深。": "먼저 파트너를 선택하고, 첫 번째 스킬을 뽑은 후, 전투, 멘토, 제작, 거래와 여섯 주요 지역을 한 번에 펼칩니다. 사람들이 정말 멈출 수 없게 만드는 것은 기능이 얼마나 많은지가 아니라, 이 세계가 당신이 어떻게 플레이했는지를 기억하고, 그 다음 길이 점점 더 깊어지는 것입니다.",
            "前往 Renaiss": "Renaiss로 이동",
            "回首頁": "메인 페이지로 돌아가기",
            "Renaiss World · Choose your future, raise your partner, and watch the world shift after every step.": "Renaiss World · 미래를 선택하고, 파트너를 키우며, 모든 단계마다 세계가 변하는 것을 지켜보세요.",
            "這不是背景換色，而是同一個世界在四種氣候裡露出四種節奏。晴空讓你推進，降雨帶來變數，旱象逼你精算，降雪把每一步都壓得更重。": "단순한 배경 교체가 아닙니다. 같은 세계가 네 가지 기후에서 서로 다른 리듬을 드러냅니다. 맑은 하늘은 전진을 돕고, 비는 변수를 만들고, 가뭄은 계산을 강요하며, 눈은 모든 선택을 더 무겁게 만듭니다.",
            "同一條路，氣候一變，打法就跟著變。": "같은 길이라도 기후가 바뀌면 플레이 방식도 바뀝니다.",
            "晴空 / Clear Sky · 推進期": "맑음 · 전진 단계",
            "視野乾淨，節奏平穩，適合推主線、探圖、整理資源，像替下一段冒險先鋪好路。": "시야가 깨끗하고 흐름이 안정적이라 메인 진행, 탐색, 자원 정리에 적합합니다. 다음 모험을 위한 길을 미리 닦는 단계입니다.",
            "降雨 / Rainfall · 變數期": "강우 · 변수 단계",
            "光線、路面與事件節奏都開始變動，適合快推、快收、快離場，每一步都更講究判斷。": "빛, 지형, 이벤트 흐름이 흔들리기 시작합니다. 빠르게 밀고, 빠르게 회수하고, 빠르게 빠지는 판단이 중요합니다.",
            "旱象 / Drought · 緊縮期": "가뭄 · 압박 단계",
            "補給與撤退都變得尖銳，錯一步就會被放大。這種氣候會逼你把每個選擇算得更狠。": "보급과 후퇴가 더 날카로운 선택이 됩니다. 한 번의 실수가 커지기 때문에 모든 결정을 더 냉정하게 계산해야 합니다.",
            "降雪 / Snowfall · 試煉期": "강설 · 시련 단계",
            "節奏放慢、能見度壓低，但也讓每一步都更有重量。真正的判斷力，會在這種時候被看見。": "속도는 느려지고 시야는 낮아지지만, 그만큼 모든 걸음의 무게가 커집니다. 진짜 판단력은 이런 순간에 드러납니다."
      }
};


    const GAME_TRANSLATION_OVERRIDES = {
      "zh-Hans": {
        "所以在": "所以在 ",
        "裡，你和夥伴不是只去探險。你是在調查來源、守住真偽、拆穿供應鏈裡的假象；每一次探索、交易、戰鬥、撤退，都會改寫下一段劇情。": "里，你和伙伴不只是去探险。你是在调查来源、守住真伪、拆穿供应链里的假象；每一次探索、交易、战斗、撤退，都会改写下一段剧情。",
        "加入 Discord": "加入 Discord"
      },
      en: {
        "但在明面秩序之外，另一股勢力正與既有體系長期角力。它們在各區節點滲透、造假、放出低價誘惑，試著把來源、鑑定與信任一點一點拆掉。": "Beyond the visible order, another force has been fighting the existing system for a long time. It infiltrates regional nodes, forges records, and uses cheap bait to slowly break down provenance, authentication, and trust.",
        "所以在": "So in ",
        "裡，你和夥伴不是只去探險。你是在調查來源、守住真偽、拆穿供應鏈裡的假象；每一次探索、交易、戰鬥、撤退，都會改寫下一段劇情。": ", you and your partner are not just exploring. You investigate provenance, protect authenticity, and expose illusions inside the supply chain; every exploration, trade, battle, and retreat rewrites the next part of the story.",
        "這是開放世界，沒有固定主線按鈕。章節、流言、戰況與角色命運都由你的選擇被動推進，最後變成所有玩家都看得見的長期傳聞。": "This is an open world with no fixed main-quest button. Chapters, rumors, battle conditions, and character fates are pushed forward by your choices, eventually becoming long-running rumors visible to every player.",
        "加入 Discord": "Join Discord"
      },
      ko: {
        "但在明面秩序之外，另一股勢力正與既有體系長期角力。它們在各區節點滲透、造假、放出低價誘惑，試著把來源、鑑定與信任一點一點拆掉。": "겉으로 보이는 질서 밖에서는 또 다른 세력이 기존 체계와 오래 싸우고 있습니다. 그들은 각 지역 거점에 침투하고, 위조하고, 낮은 가격의 유혹을 던지며 출처, 감정, 신뢰를 조금씩 무너뜨리려 합니다.",
        "所以在": "그래서 ",
        "裡，你和夥伴不是只去探險。你是在調查來源、守住真偽、拆穿供應鏈裡的假象；每一次探索、交易、戰鬥、撤退，都會改寫下一段劇情。": "에서 당신과 파트너는 단순히 탐험만 하는 것이 아닙니다. 출처를 조사하고, 진위를 지키며, 공급망 속 허상을 밝혀냅니다. 탐험, 거래, 전투, 후퇴 하나하나가 다음 이야기를 다시 씁니다.",
        "這是開放世界，沒有固定主線按鈕。章節、流言、戰況與角色命運都由你的選擇被動推進，最後變成所有玩家都看得見的長期傳聞。": "이곳은 고정된 메인 퀘스트 버튼이 없는 오픈월드입니다. 챕터, 소문, 전황, 캐릭터의 운명은 당신의 선택으로 밀려 나아가고, 결국 모든 플레이어가 볼 수 있는 장기적인 소문이 됩니다.",
        "加入 Discord": "Discord 참여"
      }
    };

    Object.entries(GAME_TRANSLATION_OVERRIDES).forEach(([lang, rows]) => {
      GAME_UI_TRANSLATIONS[lang] = Object.assign(GAME_UI_TRANSLATIONS[lang] || {}, rows);
    });

    function normalizeUiLang(raw) {
      const text = String(raw || "").trim().toLowerCase();
      if (!text) return "zh-Hant";
      if (text.startsWith("zh-hant") || text === "zh-tw" || text === "zh-hk" || text === "zh-mo") return "zh-Hant";
      if (text.startsWith("zh")) return "zh-Hans";
      if (text.startsWith("ko")) return "ko";
      if (text.startsWith("en")) return "en";
      return "zh-Hant";
    }

    function readSavedUiLang() {
      const search = new URLSearchParams(window.location.search || "");
      const fromQuery = search.get("lang") || "";
      let saved = "";
      try {
        saved = String(localStorage.getItem(INTEL_LANG_STORAGE_KEY) || "").trim();
      } catch (_error) {
        saved = "";
      }
      return normalizeUiLang(fromQuery || saved || document.documentElement.lang || navigator.language || "zh-Hant");
    }

    let currentUiLang = readSavedUiLang();
    document.documentElement.lang = currentUiLang;

    function saveUiLang(lang) {
      currentUiLang = normalizeUiLang(lang);
      document.documentElement.lang = currentUiLang;
      try {
        localStorage.setItem(INTEL_LANG_STORAGE_KEY, currentUiLang);
      } catch (_error) {}
      return currentUiLang;
    }
    saveUiLang(currentUiLang);

    function shouldTranslateTextNode(node) {
      if (!node || node.nodeType !== Node.TEXT_NODE) return false;
      const parent = node.parentElement;
      if (!parent) return false;
      if (parent.closest("[data-no-i18n='1']")) return false;
      const tag = String(parent.tagName || "").toUpperCase();
      if (["SCRIPT", "STYLE", "NOSCRIPT", "CODE", "PRE", "TEXTAREA", "OPTION"].includes(tag)) return false;
      const text = String(node.nodeValue || "").replace(/\s+/g, " ").trim();
      if (!text || text.length < 2) return false;
      if (/^https?:\/\//i.test(text)) return false;
      return true;
    }

    function collectTranslatableTextNodes(root) {
      const nodes = [];
      const walker = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT, {
        acceptNode(node) {
          return shouldTranslateTextNode(node) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
        },
      });
      while (walker.nextNode()) nodes.push(walker.currentNode);
      return nodes;
    }

    async function translateTextsForUi(lang, texts) {
      const tag = normalizeUiLang(lang);
      const rows = Array.isArray(texts) ? texts.map((x) => String(x || "")) : [];
      if (tag === "zh-Hant") return rows;
      return rows.map((text) => {
        if (!text) return text;
        const key = `${tag}\n${text}`;
        const local = GAME_UI_TRANSLATIONS[tag]?.[text];
        if (local) {
          uiTranslationMemo.set(key, local);
          return local;
        }
        return uiTranslationMemo.get(key) || text;
      });
    }

    async function applyUiLanguage() {
      const version = ++uiTranslateVersion;
      const nodes = collectTranslatableTextNodes(document.body);
      const originals = nodes.map((node) => {
        const stored = uiTextNodeCache.get(node);
        const current = String(node.nodeValue || "");
        if (typeof stored === "string") {
          return stored;
        }
        uiTextNodeCache.set(node, current);
        return current;
      });
      if (currentUiLang === "zh-Hant") {
        nodes.forEach((node, idx) => {
          node.nodeValue = originals[idx];
        });
        return;
      }
      const translated = await translateTextsForUi(currentUiLang, originals);
      if (version !== uiTranslateVersion) return;
      nodes.forEach((node, idx) => {
        node.nodeValue = String(translated[idx] || originals[idx] || "");
      });
    }

    function seasonStageNames() {
      if (currentUiLang === "en") {
        return ["CLEAR SKY", "RAINFALL", "DROUGHT", "SNOWFALL"];
      }
      if (currentUiLang === "ko") {
        return ["맑음", "강우", "가뭄", "강설"];
      }
      if (currentUiLang === "zh-Hans") {
        return ["晴空", "降雨", "旱象", "降雪"];
      }
      return ["CLEAR / 晴空", "RAINFALL / 降雨", "DROUGHT / 旱象", "SNOWFALL / 降雪"];
    }

    async function syncLanguageFromSavedState() {
      const next = readSavedUiLang();
      if (next === currentUiLang) return;
      saveUiLang(next);
      try {
        await applyUiLanguage();
        window.dispatchEvent(new CustomEvent("game:langchange", { detail: { lang: currentUiLang } }));
      } catch (error) {
        console.warn("language sync failed", error);
      }
    }

    function setupLanguageSync() {
      window.addEventListener("storage", (event) => {
        if (event.key !== INTEL_LANG_STORAGE_KEY) return;
        syncLanguageFromSavedState().catch(() => {});
      });
      window.addEventListener("pageshow", () => {
        syncLanguageFromSavedState().catch(() => {});
      });
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("inview");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    document.querySelectorAll(".reveal").forEach((el) => {
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight * 0.9) {
        el.classList.add("inview");
      } else {
        observer.observe(el);
      }
    });

    function initSeasonComparator() {
      const section = document.getElementById("seasons");
      if (!section) return;
      const comparator = section.querySelector("[data-season-comparator]");
      if (!comparator) return;

      const layers = Array.from(comparator.querySelectorAll(".season-layer"));
      const divider = comparator.querySelector("[data-season-divider]");
      const progressFill = comparator.querySelector("[data-season-progress]");
      const currentLabel = comparator.querySelector("[data-season-current]");
      const indexLabel = comparator.querySelector("[data-season-index]");
      const dots = Array.from(comparator.querySelectorAll("[data-season-dot]"));

      if (!layers.length) return;
      const stageCount = layers.length;
      let ticking = false;

      function clamp01(value) {
        return Math.max(0, Math.min(1, value));
      }

      function getProgress() {
        const start = section.offsetTop;
        const distance = Math.max(1, section.offsetHeight - window.innerHeight);
        return clamp01((window.scrollY - start) / distance);
      }

      function setStageByProgress(progress) {
        const p = clamp01(progress);
        const maxIndex = stageCount - 1;
        const floatStage = p * maxIndex;
        const base = Math.floor(floatStage);
        const local = base >= maxIndex ? 1 : floatStage - base;

        layers.forEach((layer) => {
          layer.classList.remove("is-active", "is-next");
          layer.style.opacity = "0";
          layer.style.zIndex = "1";
          layer.style.clipPath = "inset(0 0 0 0)";
        });

        if (base >= maxIndex) {
          const layer = layers[maxIndex];
          layer.classList.add("is-active");
          layer.style.opacity = "1";
          layer.style.zIndex = "3";
          if (divider) divider.style.opacity = "0";
        } else {
          const current = layers[base];
          const next = layers[base + 1];
          const leftInset = clamp01(1 - local) * 100;

          current.classList.add("is-active");
          current.style.opacity = "1";
          current.style.zIndex = "2";

          next.classList.add("is-next");
          next.style.opacity = "1";
          next.style.zIndex = "3";
          next.style.clipPath = `inset(0 0 0 ${leftInset}%)`;

          if (divider) {
            divider.style.opacity = "1";
            divider.style.left = `${leftInset}%`;
          }
        }

        const activeStage = Math.min(maxIndex, Math.round(floatStage));
        const names = seasonStageNames();
        if (currentLabel) currentLabel.textContent = names[activeStage] || `STAGE ${activeStage + 1}`;
        if (indexLabel) indexLabel.textContent = `${String(activeStage + 1).padStart(2, "0")} / ${String(stageCount).padStart(2, "0")}`;
        if (progressFill) progressFill.style.width = `${Math.round(p * 100)}%`;
        dots.forEach((dot, i) => dot.classList.toggle("is-active", i === activeStage));
      }

      function update() {
        setStageByProgress(getProgress());
      }

      function onScroll() {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(() => {
          ticking = false;
          update();
        });
      }

      dots.forEach((dot, idx) => {
        dot.addEventListener("click", () => {
          const distance = Math.max(1, section.offsetHeight - window.innerHeight);
          const ratio = idx / Math.max(1, stageCount - 1);
          const target = section.offsetTop + distance * ratio;
          window.scrollTo({ top: target, behavior: "smooth" });
        });
      });

      window.addEventListener("scroll", onScroll, { passive: true });
      window.addEventListener("resize", update, { passive: true });
      window.addEventListener("game:langchange", update);
      update();
    }

    function initScrollyLayouts() {
      const layouts = document.querySelectorAll("[data-scrolly]");
      layouts.forEach((layout) => {
        const section = layout.closest(".chapter");
        if (!section) return;
        const mode = String(layout.dataset.scrollyMode || "comparator").trim().toLowerCase();
        const isStackLayout = mode === "stack";
        const track = layout.querySelector(".scrolly-track");
        if (!track) return;
        const items = Array.from(layout.querySelectorAll(".scrolly-item"));
        if (!items.length) return;
        const cards = items.map((item) => item.querySelector(".scrolly-card")).filter(Boolean);
        if (!cards.length) return;
        const fill = layout.querySelector("[data-scrolly-fill]");
        const counter = layout.querySelector("[data-scrolly-count]");
        const desktopQuery = window.matchMedia("(min-width: 981px)");
        let divider = track.querySelector(".scrolly-wipe-divider");
        if (!divider) {
          divider = document.createElement("div");
          divider.className = "scrolly-wipe-divider";
          track.appendChild(divider);
        }
        let nav = track.querySelector(".scrolly-stage-nav");
        if (!nav) {
          nav = document.createElement("div");
          nav.className = "scrolly-stage-nav";
          cards.forEach((_, idx) => {
            const dot = document.createElement("button");
            dot.className = "scrolly-stage-dot";
            dot.type = "button";
            dot.setAttribute("aria-label", `Go to stage ${idx + 1}`);
            dot.dataset.scrollyDot = String(idx);
            nav.appendChild(dot);
          });
          track.appendChild(nav);
        }
        const dots = Array.from(nav.querySelectorAll("[data-scrolly-dot]"));
        let activeIndex = 0;
        let ticking = false;
        let isDesktopMode = false;

        function clamp01(value) {
          return Math.max(0, Math.min(1, value));
        }

        function updateMeter(index, progress) {
          const safe = Math.max(0, Math.min(index, cards.length - 1));
          const pct = Math.max(0, Math.min(1, progress));
          activeIndex = safe;
          if (fill) fill.style.width = `${Math.round(pct * 100)}%`;
          if (counter) counter.textContent = `${String(safe + 1).padStart(2, "0")} / ${String(cards.length).padStart(2, "0")}`;
          dots.forEach((dot, i) => dot.classList.toggle("is-active", i === safe));
        }

        function setActive(index) {
          const safe = Math.max(0, Math.min(index, items.length - 1));
          items.forEach((item, i) => {
            item.classList.toggle("is-active", i === safe);
            item.classList.toggle("is-past", i < safe);
            item.classList.toggle("is-next", i === safe + 1);
          });
          const progress = items.length === 1 ? 1 : safe / Math.max(1, items.length - 1);
          updateMeter(safe, progress);
        }

        function setSectionHeight() {
          if (!isDesktopMode || isStackLayout) {
            section.style.minHeight = "";
            delete section.dataset.scrollyHeight;
            return;
          }
          const perStage = Math.max(window.innerHeight * 0.9, 680);
          const totalHeight = perStage * Math.max(1, cards.length - 1) + window.innerHeight * 1.15;
          const px = `${Math.round(totalHeight)}px`;
          if (section.dataset.scrollyHeight !== px) {
            section.style.minHeight = px;
            section.dataset.scrollyHeight = px;
          }
        }

        function getProgress() {
          const start = section.offsetTop;
          const distance = Math.max(1, section.offsetHeight - window.innerHeight);
          return clamp01((window.scrollY - start) / distance);
        }

        function findNearestVisibleIndexInTrack() {
          const rect = track.getBoundingClientRect();
          const centerY = rect.top + rect.height * 0.42;
          let best = 0;
          let bestDist = Infinity;
          items.forEach((item, idx) => {
            const itemRect = item.getBoundingClientRect();
            const dist = Math.abs(itemRect.top + itemRect.height * 0.5 - centerY);
            if (dist < bestDist) {
              bestDist = dist;
              best = idx;
            }
          });
          return best;
        }

        function renderComparator(progress) {
          const p = clamp01(progress);
          const maxIndex = cards.length - 1;
          const floatStage = p * maxIndex;
          const base = Math.floor(floatStage);
          const local = base >= maxIndex ? 1 : floatStage - base;

          cards.forEach((card, i) => {
            card.style.opacity = "0";
            card.style.zIndex = "1";
            card.style.clipPath = "inset(0 0 0 0)";
            items[i].classList.remove("is-active", "is-past", "is-next");
          });

          if (base >= maxIndex) {
            cards[maxIndex].style.opacity = "1";
            cards[maxIndex].style.zIndex = "3";
            items[maxIndex].classList.add("is-active");
            if (divider) divider.style.opacity = "0";
          } else {
            const current = cards[base];
            const next = cards[base + 1];
            const leftInset = clamp01(1 - local) * 100;

            current.style.opacity = "1";
            current.style.zIndex = "2";
            next.style.opacity = "1";
            next.style.zIndex = "3";
            next.style.clipPath = `inset(0 0 0 ${leftInset}%)`;

            items[base].classList.add("is-active");
            items[base + 1].classList.add("is-next");
            for (let i = 0; i < base; i++) items[i].classList.add("is-past");

            if (divider) {
              divider.style.opacity = "1";
              divider.style.left = `${leftInset}%`;
            }
          }

          const focus = Math.min(maxIndex, Math.round(floatStage));
          updateMeter(focus, p);
        }

        function findNearestVisibleIndex() {
          const centerY = window.innerHeight * 0.5;
          let best = 0;
          let bestDist = Infinity;
          items.forEach((item, idx) => {
            const rect = item.getBoundingClientRect();
            const dist = Math.abs(rect.top + rect.height * 0.5 - centerY);
            if (dist < bestDist) {
              bestDist = dist;
              best = idx;
            }
          });
          return best;
        }

        function applyMode() {
          const shouldDesktop = desktopQuery.matches;
          if (shouldDesktop === isDesktopMode) return;
          isDesktopMode = shouldDesktop;
          layout.classList.toggle("is-comparator", isDesktopMode && !isStackLayout);
          layout.classList.toggle("is-stack", isDesktopMode && isStackLayout);
          section.classList.toggle("scrolly-chapter", isDesktopMode && !isStackLayout);
          if (!isDesktopMode) {
            cards.forEach((card) => {
              card.style.opacity = "1";
              card.style.zIndex = "1";
              card.style.clipPath = "inset(0 0 0 0)";
            });
            if (divider) divider.style.opacity = "0";
          } else if (isStackLayout) {
            cards.forEach((card) => {
              card.style.opacity = "1";
              card.style.zIndex = "1";
              card.style.clipPath = "inset(0 0 0 0)";
            });
            if (divider) divider.style.opacity = "0";
          }
          setSectionHeight();
        }

        function update() {
          applyMode();
          if (isDesktopMode && !isStackLayout) {
            renderComparator(getProgress());
          } else if (isDesktopMode && isStackLayout) {
            setActive(findNearestVisibleIndexInTrack());
          } else {
            setActive(findNearestVisibleIndex());
          }
        }

        function onScroll() {
          if (ticking) return;
          ticking = true;
          requestAnimationFrame(() => {
            ticking = false;
            update();
          });
        }

        dots.forEach((dot, idx) => {
          dot.addEventListener("click", () => {
            if (!isDesktopMode || isStackLayout) {
              items[idx]?.scrollIntoView({ behavior: "smooth", block: "center" });
              return;
            }
            const distance = Math.max(1, section.offsetHeight - window.innerHeight);
            const ratio = idx / Math.max(1, cards.length - 1);
            const target = section.offsetTop + distance * ratio;
            window.scrollTo({ top: target, behavior: "smooth" });
          });
        });

        window.addEventListener("scroll", onScroll, { passive: true });
        track.addEventListener("scroll", onScroll, { passive: true });
        window.addEventListener("resize", () => {
          setSectionHeight();
          update();
        }, { passive: true });
        update();
      });
    }

    requestAnimationFrame(() => {
      document.body.classList.add("page-ready");
    });

    setupLanguageSync();
    applyUiLanguage().catch(() => {});
    initSeasonComparator();
    initScrollyLayouts();
