/*
this would expand all submenus

this code only 1/2 works, it breaks on phones
see the following for a phone friendly version

https://github.com/squidfunk/mkdocs-material/issues/767
*/

/*
document.addEventListener("DOMContentLoaded", function() {
    var nav = document.getElementsByClassName("md-nav");
    for(var i = 0; i < nav.length; i++) {
        if (nav.item(i).getAttribute("data-md-level")) {
            nav.item(i).style.display = 'block';
            nav.item(i).style.overflow = 'visible';
        }
    }

    var nav = document.getElementsByClassName("md-nav__toggle");
    for(var i = 0; i < nav.length; i++) {
       nav.item(i).checked = true;
    }
});
*/
