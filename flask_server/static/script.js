const socket = io();

let controlMode = "focus";

let currentIndex = 0;

let total = 0;


// 顯示指定分類
function showCategory(category) {

    let cards = document.querySelectorAll('.menu-card');

    cards.forEach(function(card) {

        if (category === 'all') {

            card.style.display = "block";

        }

        else if (card.classList.contains(category)) {

            card.style.display = "block";

        }

        else {

            card.style.display = "none";
        }

    });
}


// 增加數量
function increase(button, price) {

    let quantityText =
        button.parentElement.querySelector('.quantity');

    let quantity =
        parseInt(quantityText.innerText);

    quantity++;

    quantityText.innerText = quantity;

    total += price;

    updateTotal();
}


// 減少數量
function decrease(button, price) {

    let quantityText =
        button.parentElement.querySelector('.quantity');

    let quantity =
        parseInt(quantityText.innerText);

    if (quantity > 0) {

        quantity--;

        quantityText.innerText = quantity;

        total -= price;

        updateTotal();
    }
}


// 更新總金額
function updateTotal() {

    document.getElementById('total-price').innerText =
        "$" + total;
}


// 設定模式
function setMode(mode) {

    controlMode = mode;

    document.getElementById('mode-text').innerText =
        controlMode;
}


// 更新選中框
function updateSelection() {

    let cards = document.querySelectorAll('.menu-card');

    cards.forEach(card => {

        card.classList.remove('selected');

    });

    cards[currentIndex].classList.add('selected');
}


// 增加目前商品
function increaseCurrent() {

    let cards = document.querySelectorAll('.menu-card');

    let currentCard = cards[currentIndex];

    let plusButton =
        currentCard.querySelectorAll('button')[1];

    plusButton.click();
}


// 減少目前商品
function decreaseCurrent() {

    let cards = document.querySelectorAll('.menu-card');

    let currentCard = cards[currentIndex];

    let minusButton =
        currentCard.querySelectorAll('button')[0];

    minusButton.click();
}


// 接收 Focus 更新
socket.on("focus_update", function(data) {

    console.log(data);


    // MOVE
    if(data.type === "MOVE") {

        currentIndex = data.index;

        updateSelection();

        document.getElementById("status-text").innerText =
            "Move Focus";
    }


    // INCREASE
    else if(data.type === "INCREASE") {

        currentIndex = data.index;

        updateSelection();

        increaseCurrent();

        document.getElementById("status-text").innerText =
            "Increase Item";
    }


    // DECREASE
    else if(data.type === "DECREASE") {

        currentIndex = data.index;

        updateSelection();

        decreaseCurrent();

        document.getElementById("status-text").innerText =
            "Decrease Item";
    }


    // SELECT
    else if(data.type === "SELECT") {

        currentIndex = data.index;

        updateSelection();

        document.getElementById("status-text").innerText =
            "Select Item";
    }
});