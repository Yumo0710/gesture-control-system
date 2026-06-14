const socket = io();

let controlMode = "focus";
let currentIndex = 0;
let total = 0;


// 顯示指定分類；這只改變畫面顯示，不改變後端 FocusMode 的索引。
function showCategory(category) {
    const cards = document.querySelectorAll(".menu-card");

    cards.forEach(function(card) {
        if (category === "all" || card.classList.contains(category)) {
            card.style.display = "block";
        } else {
            card.style.display = "none";
        }
    });

    updateSelection();
}


// 增加餐點數量並同步總金額。
function increase(button, price) {
    const quantityText = button.parentElement.querySelector(".quantity");
    let quantity = parseInt(quantityText.innerText, 10);

    quantity += 1;
    quantityText.innerText = quantity;
    total += price;
    updateTotal();
}


// 減少餐點數量時不允許低於 0，避免總金額變成負數。
function decrease(button, price) {
    const quantityText = button.parentElement.querySelector(".quantity");
    let quantity = parseInt(quantityText.innerText, 10);

    if (quantity > 0) {
        quantity -= 1;
        quantityText.innerText = quantity;
        total -= price;
        updateTotal();
    }
}


// 更新總金額顯示，讓手勢與滑鼠點擊共用同一套邏輯。
function updateTotal() {
    document.getElementById("total-price").innerText = "$" + total;
}


// 切換控制模式並通知後端，讓 Python 主程式同步進入 Focus 或 Mouse 流程。
function setMode(mode) {
    if (mode !== "focus" && mode !== "mouse") {
        return;
    }

    controlMode = mode;
    applyModeState();
    socket.emit("mode_change", { mode: controlMode });
}


// 統一更新模式文字、按鈕狀態與 Mouse Mode 大按鈕樣式。
function applyModeState() {
    document.getElementById("mode-text").innerText = controlMode === "focus" ? "Focus" : "Mouse";
    document.body.classList.toggle("mouse-mode", controlMode === "mouse");
    updateModeButtons();
}


function updateModeButtons() {
    const buttons = document.querySelectorAll(".mode-bar button");

    buttons.forEach(button => {
        const mode = button.dataset.mode;
        button.classList.toggle("active", mode === controlMode);
        button.setAttribute("aria-pressed", mode === controlMode ? "true" : "false");
    });
}


// 更新目前選取卡片；若卡片被分類隱藏，就不強制改變索引。
function updateSelection() {
    const cards = document.querySelectorAll(".menu-card");

    cards.forEach(card => {
        card.classList.remove("selected");
    });

    if (cards[currentIndex] && cards[currentIndex].style.display !== "none") {
        cards[currentIndex].classList.add("selected");
        cards[currentIndex].scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
}


// 對目前 Focus 的餐點執行增加數量。
function increaseCurrent() {
    const cards = document.querySelectorAll(".menu-card");
    const currentCard = cards[currentIndex];

    if (!currentCard) {
        return;
    }

    const plusButton = currentCard.querySelectorAll("button")[1];
    plusButton.click();
}


// 對目前 Focus 的餐點執行減少數量。
function decreaseCurrent() {
    const cards = document.querySelectorAll(".menu-card");
    const currentCard = cards[currentIndex];

    if (!currentCard) {
        return;
    }

    const minusButton = currentCard.querySelectorAll("button")[0];
    minusButton.click();
}


// 模式切換方法之一：鍵盤快捷鍵，方便測試時不用移動滑鼠。
document.addEventListener("keydown", function(event) {
    const key = event.key.toLowerCase();

    if (key === "f") {
        setMode("focus");
        document.getElementById("status-text").innerText = "已用鍵盤切到 Focus Mode";
    } else if (key === "m") {
        setMode("mouse");
        document.getElementById("status-text").innerText = "已用鍵盤切到 Virtual Mouse";
    }
});


// 接收後端模式切換結果，確保手勢切換、按鈕切換和鍵盤切換都同步 UI。
socket.on("mode_changed", function(data) {
    controlMode = data.mode;
    applyModeState();

    document.getElementById("status-text").innerText =
        controlMode === "focus" ? "Focus Mode 已啟用" : "Virtual Mouse 已啟用";
});


// 接收 Focus Mode 的手勢更新，依照後端結果移動選取或調整數量。
socket.on("focus_update", function(data) {
    if (data.type === "MOVE") {
        currentIndex = data.index;
        updateSelection();
        document.getElementById("status-text").innerText = "已切換餐點";
    } else if (data.type === "INCREASE") {
        currentIndex = data.index;
        updateSelection();
        increaseCurrent();
        document.getElementById("status-text").innerText = "已增加數量";
    } else if (data.type === "DECREASE") {
        currentIndex = data.index;
        updateSelection();
        decreaseCurrent();
        document.getElementById("status-text").innerText = "已減少數量";
    } else if (data.type === "SELECT") {
        currentIndex = data.index;
        updateSelection();
        document.getElementById("status-text").innerText = "已選取餐點";
    }
});


// 初始狀態先標示 Focus Mode 與第一張餐點卡，讓使用者知道目前控制位置。
applyModeState();
updateSelection();
