const socket = io();

let controlMode = "focus";

let currentIndex = 0;

let total = 0;

let currentView = "menu";


function getCards() {

    return Array.from(document.querySelectorAll(".menu-card"));
}


function getVisibleCards() {

    return getCards().filter(card => card.style.display !== "none");
}


// 顯示指定分類，切換分類後會把焦點重設到目前可見的第一個商品。
function showCategory(category) {

    let cards = getCards();

    cards.forEach(function(card) {

        if (category === "all" || card.classList.contains(category)) {

            card.style.display = "block";

        }

        else {

            card.style.display = "none";
        }

    });

    currentIndex = 0;

    updateSelection();

    setStatus("已切換分類");
}


// 增加數量並同步更新總金額。
function increase(button, price) {

    let quantityText =
        button.parentElement.querySelector(".quantity");

    let quantity =
        parseInt(quantityText.innerText);

    quantity++;

    quantityText.innerText = quantity;

    total += price;

    updateTotal();
}


// 減少數量時不可低於 0，避免總金額出現負數。
function decrease(button, price) {

    let quantityText =
        button.parentElement.querySelector(".quantity");

    let quantity =
        parseInt(quantityText.innerText);

    if (quantity > 0) {

        quantity--;

        quantityText.innerText = quantity;

        total -= price;

        updateTotal();
    }
}


// 更新底部與結帳畫面的總金額。
function updateTotal() {

    document.getElementById("total-price").innerText =
        "$" + total;

    document.getElementById("checkout-total-price").innerText =
        "$" + total;
}


// 設定模式文字，目前保留 focus 與 mouse 的 UI 切換。
function setMode(mode) {

    controlMode = mode;

    document.getElementById("mode-text").innerText =
        controlMode;
}


function setStatus(text) {

    document.getElementById("status-text").innerText = text;
}


// 更新選中框，只會在目前可見商品中移動焦點。
function updateSelection() {

    let cards = getCards();

    let visibleCards = getVisibleCards();

    cards.forEach(card => {

        card.classList.remove("selected");

    });

    if (visibleCards.length === 0) {

        return;
    }

    currentIndex = ((currentIndex % visibleCards.length) + visibleCards.length) % visibleCards.length;

    visibleCards[currentIndex].classList.add("selected");
}


function getCurrentCard() {

    let visibleCards = getVisibleCards();

    if (visibleCards.length === 0) {

        return null;
    }

    currentIndex = ((currentIndex % visibleCards.length) + visibleCards.length) % visibleCards.length;

    return visibleCards[currentIndex];
}


// 增加目前商品，讓手勢與按鈕共用同一套加減邏輯。
function increaseCurrent() {

    let currentCard = getCurrentCard();

    if (!currentCard) {

        return;
    }

    let plusButton =
        currentCard.querySelectorAll("button")[1];

    plusButton.click();
}


// 減少目前商品，讓手勢與按鈕共用同一套加減邏輯。
function decreaseCurrent() {

    let currentCard = getCurrentCard();

    if (!currentCard) {

        return;
    }

    let minusButton =
        currentCard.querySelectorAll("button")[0];

    minusButton.click();
}


function getOrderItems() {

    return getCards().map(card => {

        return {
            name: card.dataset.name,
            price: parseInt(card.dataset.price),
            quantity: parseInt(card.querySelector(".quantity").innerText)
        };

    }).filter(item => item.quantity > 0);
}


// 建立訂單明細，讓完成購物畫面能呈現實際選購內容。
function renderOrderSummary() {

    let orderList = document.getElementById("order-list");

    let items = getOrderItems();

    orderList.innerHTML = "";

    if (items.length === 0) {

        orderList.innerHTML = "<p>尚未選擇商品</p>";

        return;
    }

    items.forEach(item => {

        let row = document.createElement("div");

        row.className = "order-row";

        row.innerHTML = `
            <span>${item.name} x ${item.quantity}</span>
            <strong>$${item.price * item.quantity}</strong>
        `;

        orderList.appendChild(row);
    });
}


function completeShopping() {

    if (total <= 0) {

        setStatus("請先選擇商品");

        return;
    }

    currentView = "checkout";

    renderOrderSummary();

    document.getElementById("checkout-view").classList.remove("hidden");

    setStatus("完成購物");
}


function backToMenu() {

    currentView = "menu";

    document.getElementById("checkout-view").classList.add("hidden");

    updateSelection();

    setStatus("返回點餐");
}


function handleBackGesture() {

    if (currentView === "checkout") {

        backToMenu();

        return;
    }

    showCategory("all");

    setStatus("返回首頁");
}


// 接收 Focus 更新，將後端手勢事件轉成前端頁面動作。
socket.on("focus_update", function(data) {

    console.log(data);

    if (data.type === "MOVE") {

        if (currentView !== "menu") {

            return;
        }

        currentIndex = data.index;

        updateSelection();

        setStatus("移動選取");
    }


    else if (data.type === "INCREASE") {

        if (currentView !== "menu") {

            return;
        }

        currentIndex = data.index;

        updateSelection();

        increaseCurrent();

        setStatus("增加商品");
    }


    else if (data.type === "DECREASE") {

        if (currentView !== "menu") {

            return;
        }

        currentIndex = data.index;

        updateSelection();

        decreaseCurrent();

        setStatus("減少商品");
    }


    else if (data.type === "SELECT") {

        completeShopping();
    }


    else if (data.type === "BACK") {

        handleBackGesture();
    }
});


// 頁面載入後先選中第一個商品，讓使用者一開始就能用手勢操作。
document.addEventListener("DOMContentLoaded", function() {

    updateSelection();

    updateTotal();
});
