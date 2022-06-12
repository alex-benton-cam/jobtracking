function selectMachine2(id) {


    var machField = document.getElementById("machine_id_field");
    var machCard = document.getElementById(id);

    if (machCard.hasAttribute("selected")) {
        machCard.removeAttribute("selected")
        machCard.setAttribute('class', 'card')
        machField.value = ""
    } else {
        machField.value = id;
        const cards = document.querySelectorAll('[selected="true"]');
        machCard.setAttribute('class', 'card bg-primary text-white');
        machCard.setAttribute('selected', 'true');
        
        


        for (i = 0; i < cards.length; ++i) {

            cards[i].removeAttribute("selected");
            cards[i].setAttribute('class', 'card');
        }
    }


}
