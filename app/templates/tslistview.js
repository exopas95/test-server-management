function closeAllSelect(elmnt) {
    /* A function that will close all select boxes in the document,
        except the current select box: */
    var dropdownlist, targetNode, arrNo = [], i;
    dropdownlist = document.getElementsByClassName("select-items");
    targetNode = document.getElementsByClassName("select-selected");

    for (i = 0; i < targetNode.length; i++) {
        if (elmnt == targetNode[i]) {
            arrNo.push(i)
        } else {
            targetNode[i].classList.remove("select-arrow-active");
        }
    }

    for (i = 0; i < dropdownlist.length; i++) {
        if (arrNo.indexOf(i)) {
            dropdownlist[i].classList.add("select-hide");
        }
    }
}

function modify(TSaddr, index) {
    var dropdownlist = document.getElementsByClassName("custom-select")[0].getElementsByTagName("option");
    var targetlist = document.getElementsByClassName("select-selected"), targetTas, currentUser, i, targetIndex;

    for (i = 0; i < targetlist.length; i++) {
        if (targetlist[i].parentElement.id == index) {
            targetIndex = i;
            break;
        }
    }

    for (i = 0; i < dropdownlist.length; i++) {
        if (targetlist[targetIndex].textContent == dropdownlist[i].innerHTML) {
            currentUser = dropdownlist[i].getAttribute("value");
        }
        content = dropdownlist[i].innerHTML.replace(/\s/g, '');
        if (targetlist[targetIndex+1].textContent.includes(content)) {
            targetTas = dropdownlist[i].getAttribute("value");
        }
    }

    if (currentUser == "") {
        alert("User is not selected!");
    } else if (typeof targetTas == "undefined") {
        alert("Target TAS is not selected!");
    } else {
        window.location.href = window.location.href + "modify/" + TSaddr + "/" + currentUser + "/" + targetTas;
    }
}

function lock(TSaddr) {
    window.location.href = window.location.href + "lock/" + TSaddr;
}

function unlock(TSaddr) {
    window.location.href = window.location.href + "unlock/" + TSaddr;
}

function validateIpAddr(ipAddr) {
if (/^(?!0)(?!.*\.$)((1?\d?\d|25[0-5]|2[0-4]\d)(\.|$)){4}$/.test(ipAddr)) {
  return (true)
}
  return (false)
}

function sleep(ms) {
var start = new Date().getTime();
  for (var i = 0; i < 1e7; i++) {
      if ((new Date().getTime() - start) > ms) {
        break;
      }
    }
}

function reserveing(TSaddr, relocateTAS, index, reservPerson){
    var month_1, date_1, hour_1, minute_1, ampm_1, month_2, date_2, hour_2, minute_2, ampm_2;
    month_1 = parseInt(document.getElementById("StartMonth"+index).value);
    date_1 = parseInt(document.getElementById("StartDay"+index).value);
    hour_1 = parseInt(document.getElementById("StartHour"+index).value);
    minute_1 = parseInt(document.getElementById("StartMinute"+index).value);
    ampm_1 = parseInt(document.getElementById("StartAmPm"+index).value);
    month_2 = parseInt(document.getElementById("EndMonth"+index).value);
    date_2 = parseInt(document.getElementById("EndDay"+index).value);
    hour_2 = parseInt(document.getElementById("EndHour"+index).value);
    minute_2 = parseInt(document.getElementById("EndMinute"+index).value);
    ampm_2 = parseInt(document.getElementById("EndAmPm"+index).value);
    
    window.location.href = window.location.href + "reserve/" + month_1 + "/" + date_1 + "/" + hour_1 + "/" + minute_1 + "/" + ampm_1 + "/"
                                                        + month_2 + "/" + date_2 + "/" + hour_2 + "/" + minute_2 + "/" + ampm_2 + "/" 
                                                        + TSaddr + "/" + relocateTAS + "/" + reservPerson;
    }

function cancelReserve(TSaddr, index){
    window.location.href = window.location.href + "cancelReserve/" + TSaddr + "/" + parseint(index);
}

