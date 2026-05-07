let controlMode = "focus"; // 控制模式
let currentIndex = 0; // 選中框參數
let total = 0; // 金額參數

//顯示指定分類-------------------------------
function showCategory(category) {

    // 取得所有商品卡片
    let cards = document.querySelectorAll('.menu-card');


    // 一張一張檢查
    cards.forEach(function(card) {

        // 如果是全部
        if (category === 'all') {

            card.style.display = "block";

        }

        // 顯示對應分類
        else if (card.classList.contains(category)) {

            card.style.display = "block";

        }

        // 其他隱藏
        else {

            card.style.display = "none";

        }

    });

}
//顯示指定分類-------------------------------



// 金額、數量改變-----------------------------
function increase(button, price) {

    // 找到數量文字
    let quantityText =
        button.parentElement.querySelector('.quantity');

    // 取得目前數量
    let quantity = parseInt(quantityText.innerText);

    // +1
    quantity++;

    // 更新畫面
    quantityText.innerText = quantity;

    // 增加總金額
    total += price;

    // 更新總金額畫面
    updateTotal();
}


// 減少數量
function decrease(button, price) {

    let quantityText =
        button.parentElement.querySelector('.quantity');

    let quantity = parseInt(quantityText.innerText);

    // 避免變負數
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
// 金額、數量改變-----------------------------

//顯示當前控制模式-------------------------------
function setMode(mode) {

    controlMode = mode;

    console.log("目前模式:", controlMode);
    // 更新畫面文字
    document.getElementById('mode-text').innerText =
        controlMode;
}
//顯示當前控制模式-------------------------------

//焦點控制模式--------------------------------
function updateSelection() {

    let cards = document.querySelectorAll('.menu-card');

    // 先清空全部選中
    cards.forEach(card => {
        card.classList.remove('selected');
    });

    // 加入新的選中框
    cards[currentIndex].classList.add('selected');
}

function moveRight() {

    // 如果不是焦點模式
    if (controlMode !== "focus") {
        return;
    }

    let cards = document.querySelectorAll('.menu-card');

    currentIndex++;

    if (currentIndex >= cards.length) {
        currentIndex = 0;
    }

    updateSelection();
}
function moveLeft() {

    // 如果不是焦點模式
    if (controlMode !== "focus") {
        return;
    }

    let cards = document.querySelectorAll('.menu-card');

    currentIndex--;

    // 小於 0 就回最後一個
    if (currentIndex < 0) {

        currentIndex = cards.length - 1;
    }

    updateSelection();
}
// 增加目前選中商品
function increaseCurrent() {

    // 如果不是焦點模式
    if (controlMode !== "focus") {
        return;
    }

    // 取得所有商品卡片
    let cards = document.querySelectorAll('.menu-card');

    // 取得目前選中商品
    let currentCard = cards[currentIndex];

    // 找到 + 按鈕
    let plusButton =
        currentCard.querySelectorAll('button')[1];

    // 模擬點擊 +
    plusButton.click();
}
// 減少目前選中商品
function decreaseCurrent() {

    // 如果不是焦點模式
    if (controlMode !== "focus") {
        return;
    }

    let cards = document.querySelectorAll('.menu-card');

    let currentCard = cards[currentIndex];

    // 找到 - 按鈕
    let minusButton =
        currentCard.querySelectorAll('button')[0];

    // 模擬點擊 -
    minusButton.click();
}
document.addEventListener('keydown', function(event) {

    // 右方向鍵
    if (event.key === 'ArrowRight') {

        moveRight();
    }

    // 左方向鍵
    else if (event.key === 'ArrowLeft') {

        moveLeft();
    }

    // Enter 鍵
    else if (event.key === 'Enter') {

        increaseCurrent();
    }

    // Backspace 鍵
    else if (event.key === 'Backspace') {

        decreaseCurrent();
    }

});
//焦點控制模式--------------------------------