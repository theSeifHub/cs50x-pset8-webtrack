let cold = {
    Guava: 20,
    Mango: 35,
    Strawberry: 15,
    Cocacola: 7,
};
function insert(id) {
    if ("content" in document.createElement("template")) {
        let temp = document.querySelector("#oneCol");
        let tableToInsert = document.querySelector(`#${id}`);
        let frag = document.createDocumentFragment();
        // console.log(Object.entries(cold).length);
        for (const [bev, price] of Object.entries(cold)) {
            let cloneRow = temp.content.cloneNode(true).querySelector("tr");
            let cloneCells = cloneRow.querySelectorAll("td");
            cloneCells[0].textContent = bev;
            cloneCells[1].textContent = price;
            frag.appendChild(cloneRow);
            // console.log(bev, price);
        }
        tableToInsert.querySelector("table").appendChild(frag);
    }
}
insert("cold-beverage");