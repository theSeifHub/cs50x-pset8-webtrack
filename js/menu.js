// Returns the requested menu section
function menuSection(item) {
    const menuItems = {
        "hotBev": {
            "Shay (Tea)": 2.5,
            "Shay Ne'naa' (Tea+Mint)": 3,
            "Shay Belabn (Tea+Milk)": 4,
            "Coffee": 4,
            "Sakalans (Tea+Coffee)": 6,
            "Nescafe": 5,
            "Sahlab (Salep)": 7,
            "Cocoa": 5,
            "Helba (Fenugreek)": 3,
            "Yansoun (Anise Tea)": 4,
            "Ne'naa' (Mint Tea)": 4,
            "Karkaday (Hibiscus Tea)": 4,
            "Qirfa (Cinnamon)": 5,
            "Zanjbeel (Ginger)": 5
        },
        "coldBev": {
            "Enaab (Cold Hibiscus)": 5,
            "Tamr (Tamarind)": 5,
            "Lemon juice": 5,
            "Guava juice": 8,
            "Mango juice": 10,
            "Strawberry juice": 10,
            "Mooz Belabn (Banana Milkshake)": 10,
            "Cold Cocoa": 6,
            "Fizzy drink bottle": 4,
            "Fizzy drink can": 5,
            "Birell malt beverage": 6,
            "Fayrouz malt beverage": 6
        },
        "shisha": {
            "Qas (Molasses soaked)": 3,
            "Saloum (Light Qas)": 3,
            "Tefaah (Apple flavor)": 5,
            "Khoukh (Peach flavor)": 5,
            "Lemon flavor": 5,
            "Ne'naa' (Mint flavor)": 5
        },
        "sandwiches": {
            "Kebda (Liver)": 7,
            "Sausage": 8,
            "Mombar (Rice sausage)": 7,
            "Hawawshi": 10,
            "Batates (French fries)": 5,
            "Extra Tahini": 3,
            "Extra Salad & Pickles": 2
        }
    };
    return menuItems[item];
}

// Inserts menu items in each section table
function insertItems(id) {
    if ("content" in document.createElement("template")) {
        const temp = document.querySelector("template"),
            column = document.querySelector(`#${id}`).querySelector(".column"),
            // cloning column in case of a long list
            items = Object.entries(menuSection(id)),
            itemsCount = items.length;
        // console.log(column, columnClone);
        let frag = document.createDocumentFragment(),
            columnClone;
        for (const [i, [bev, price]] of items.entries()) {
            // for long lists, when reach the middle item:
            // insert the table in the first column
            // and empty the fragment to be used by the second table
            if (itemsCount > 10 && i === itemsCount / 2) {
                columnClone = column.cloneNode(true);
                column.querySelector("table").appendChild(frag);
                frag.innerHTML = '';
            }
            let cloneRow = temp.content.cloneNode(true).querySelector("tr"),
                cloneCells = cloneRow.querySelectorAll("td");
            cloneCells[0].textContent = bev;
            cloneCells[1].textContent = price;
            frag.appendChild(cloneRow);
        }
        // Insert the second table if items are more than 10
        if (itemsCount > 10) {
            columnClone.querySelector("table").appendChild(frag);
            column.insertAdjacentElement('afterend', columnClone);
        } else { column.querySelector("table").appendChild(frag); }
    }
}

// Populate all the tabs
(function () {
    const menu = ["coldBev", "hotBev", "shisha", "sandwiches"];
    menu.forEach((section) => insertItems(section));
})();

// Open the tab when clicked
function openMenu(sectionName, elmnt) {
    // Hide all elements with class="tabcontent" by default
    let i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Restore changed styles of all tablinks/buttons
    tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].style.backgroundColor = "";
        tablinks[i].style.color = "white";
    }

    // Show the specific tab content
    document.getElementById(sectionName).style.display = "block";

    // Add the specific color to the button used to open the tab content
    elmnt.style.backgroundColor = 'transparent';
    elmnt.style.color = 'transparent';
}

// Get the element with id="defaultOpen" and click on it
document.getElementById("defaultOpen").click();