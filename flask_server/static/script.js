const socket = io();

let controlMode = "focus";
let currentIndex = 0;
let total = 0;


function getSelectableItems() {
    return Array.from(document.querySelectorAll(".selectable-item"));
}


function getMenuCards() {
    return Array.from(document.querySelectorAll(".menu-card"));
}


function getCheckoutButton() {
    return document.getElementById("checkout-button");
}


function setStatus(message) {
    document.getElementById("status-text").innerText = message;
}


// 顯示指定分類的餐點；Focus 索引仍以完整菜單為準，避免前後端索引不同步。
function showCategory(category) {
    getMenuCards().forEach(function(card) {
        if (category === "all" || card.classList.contains(category)) {
            card.style.display = "block";
        } else {
            card.style.display = "none";
        }
    });

    updateSelection();
}


// 增加目前餐點數量，按鈕點擊與上滑手勢共用這個函式。
function increase(button, price) {
    const quantityText = button.parentElement.querySelector(".quantity");
    let quantity = parseInt(quantityText.innerText, 10);

    quantity += 1;
    quantityText.innerText = quantity;
    total += price;
    updateTotal();
}


// 減少目前餐點數量，最低維持 0，避免總金額被扣成負數。
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


function updateTotal() {
    document.getElementById("total-price").innerText = "$" + total;
}


// 前端模式按鈕也會通知後端，讓手勢處理邏輯保持同一個模式狀態。
function setMode(mode) {
    if (mode !== "focus" && mode !== "mouse") {
        return;
    }

    controlMode = mode;
    applyModeState();
    socket.emit("mode_change", { mode: controlMode });
}


function applyModeState() {
    const modeText = controlMode === "focus" ? "Focus" : "Mouse";
    document.getElementById("mode-text").innerText = modeText;
    document.getElementById("footer-mode-text").innerText = modeText;
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


function clearCheckoutFocus() {
    getCheckoutButton().classList.remove("selected");
}


// Focus Mode 只高亮餐點卡片，確認餐點由 OK 手勢另外控制。
function updateSelection() {
    const items = getSelectableItems();

    clearCheckoutFocus();
    items.forEach(item => {
        item.classList.remove("selected");
    });

    const selectedItem = items[currentIndex];
    if (selectedItem) {
        selectedItem.classList.add("selected");
        selectedItem.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
}


function activateCurrentItem() {
    const items = getSelectableItems();
    const currentItem = items[currentIndex];

    if (!currentItem) {
        return;
    }

    const plusButton = currentItem.querySelectorAll("button")[1];
    if (plusButton) {
        plusButton.click();
    }
}


function decreaseCurrent() {
    const items = getSelectableItems();
    const currentItem = items[currentIndex];

    if (!currentItem) {
        return;
    }

    const minusButton = currentItem.querySelectorAll("button")[0];
    if (minusButton) {
        minusButton.click();
    }
}


function getOrderItems() {
    return getMenuCards().map(card => {
        const name = card.dataset.name;
        const price = parseInt(card.dataset.price, 10);
        const quantity = parseInt(card.querySelector(".quantity").innerText, 10);
        return {
            name,
            price,
            quantity,
            subtotal: price * quantity,
        };
    }).filter(item => item.quantity > 0);
}


function focusCheckoutButton() {
    getSelectableItems().forEach(item => {
        item.classList.remove("selected");
    });

    const checkoutButton = getCheckoutButton();
    checkoutButton.classList.add("selected");
    checkoutButton.scrollIntoView({ block: "nearest", behavior: "smooth" });
}


function isOrderModalOpen() {
    return !document.getElementById("order-modal").hidden;
}


function handleCheckoutConfirm() {
    // OK 手勢採兩段式確認：第一次開明細，明細開啟後再 OK 一次才送出訂單。
    if (isOrderModalOpen()) {
        confirmOrder();
        return;
    }

    focusCheckoutButton();
    showOrderModal();
}


function showOrderModal() {
    const orderItems = getOrderItems();
    const orderList = document.getElementById("order-list");
    const modalTotal = document.getElementById("modal-total-price");
    const modal = document.getElementById("order-modal");

    orderList.innerHTML = "";

    if (orderItems.length === 0) {
        orderList.innerHTML = '<p class="empty-order">目前尚未選擇餐點</p>';
    } else {
        orderItems.forEach(item => {
            const row = document.createElement("div");
            row.className = "order-row";
            row.innerHTML = `
                <span>${item.name}</span>
                <span>$${item.price} x ${item.quantity}</span>
                <strong>$${item.subtotal}</strong>
            `;
            orderList.appendChild(row);
        });
    }

    modalTotal.innerText = "$" + total;
    modal.hidden = false;
    setStatus("已開啟訂單明細");
}


function closeOrderModal() {
    document.getElementById("order-modal").hidden = true;
    setStatus("返回修改餐點");
}


function confirmOrder() {
    const orderItems = getOrderItems();

    if (orderItems.length === 0) {
        setStatus("請先選擇餐點");
        return;
    }

    document.getElementById("order-modal").hidden = true;
    setStatus("訂單已送出");
}


// 鍵盤快捷鍵保留給展示與除錯使用：F/M 切模式，C/Enter 確認餐點，Esc 關閉明細。
document.addEventListener("keydown", function(event) {
    const key = event.key.toLowerCase();

    if (key === "f") {
        setMode("focus");
        setStatus("已切換到 Focus Mode");
    } else if (key === "m") {
        setMode("mouse");
        setStatus("已切換到 Virtual Mouse");
    } else if (key === "c" || key === "enter") {
        handleCheckoutConfirm();
    } else if (key === "escape") {
        closeOrderModal();
    }
});


socket.on("mode_changed", function(data) {
    controlMode = data.mode;
    applyModeState();
    setStatus(controlMode === "focus" ? "Focus Mode 已啟用" : "Virtual Mouse 已啟用");
});


// 接收後端 Focus 指令：滑動只操作餐點，CHECKOUT 才聚焦確認餐點並開啟明細。
socket.on("focus_update", function(data) {
    if (data.type === "MOVE") {
        currentIndex = data.index;
        updateSelection();
        setStatus("已切換餐點");
    } else if (data.type === "INCREASE") {
        currentIndex = data.index;
        updateSelection();
        activateCurrentItem();
        setStatus("已增加數量");
    } else if (data.type === "DECREASE") {
        currentIndex = data.index;
        updateSelection();
        decreaseCurrent();
        setStatus("已減少數量");
    } else if (data.type === "CHECKOUT" || data.type === "SELECT") {
        handleCheckoutConfirm();
    }
});


applyModeState();
updateSelection();
