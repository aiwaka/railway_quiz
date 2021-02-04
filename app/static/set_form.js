(function($) {
  $(document).ready(function() {
    $('#company_select').on('change', function(){
      $.ajax({
        url: 'get_routes',
        type: 'POST',
        dataType: 'json',
        // フォーム要素の内容をハッシュ形式に変換
        data: $('form').serializeArray(),
        timeout: 5000,
      })
      .done(function(data) {
        const first_value = Object.keys(data);
        var options = $.map(data, function (ja_name, eng_name) {
          isSelected = (eng_name === first_value[0]);
          $option = $('<option>', { value: eng_name, text: ja_name, selected: isSelected });
          return $option;
        });
        $('#route_select').children().remove();
        $('#route_select').append(options);
      })
      .fail(function() {
          console.log("failed\n")
      });
    });
  });
})(jQuery);
