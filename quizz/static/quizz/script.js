$(document).ready(function() {
    $(".object-row").click(function() {
        var url = $(this).data("url");
        window.location.href = url;
    });
});

function confirmDelete() {
    return confirm("Êtes-vous sûr de vouloir supprimer cet élément ?");
}

function toggleLabelColor(label,label_color) {
    var label = $(label);


    if (label.hasClass('label-grey')) {
        label.removeClass('label-grey').addClass(label_color);
    } else {
        label.removeClass(label_color).addClass('label-grey');
    }
}

function submitFormAjax() {
    var form = $('#score-form');

    // Afficher le bandeau de chargement
    $('#loading-overlay').removeClass('d-none');

    $.ajax({
        
        type: form.attr('method'),
        url: form.attr('action'),
        data: form.serialize(),  // serialize the form data
        success: function(response) {
            $('#graph-container').html(response);
            
        },
        complete: function() {
            // Cacher le bandeau de chargement une fois le chargement terminé
            $('#loading-overlay').addClass('d-none');
        }
    });
}

$(document).ready(function() {
    // Afficher le popup pendant 3 secondes
    $('#popup').fadeIn(1000).delay(3000).fadeOut(1000);
});


