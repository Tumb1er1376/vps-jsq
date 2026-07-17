(function(){
  function markCalculated(){ document.body.classList.add('has-calculated'); }
  window.addEventListener('DOMContentLoaded', function(){
    var result=document.getElementById('result');
    if(result && 'MutationObserver' in window){
      new MutationObserver(function(){
        var v=(document.querySelector('.output_trade_date')||{}).textContent || '';
        if(v.trim() && v.trim() !== '--' && v.trim() !== '0000-00-00') markCalculated();
      }).observe(result,{childList:true,subtree:true,characterData:true});
    }
  });
})();
