//首页

define(function(require){
	var index = {
			init:function() {
				this.showMonitorInfo();
			},
			
			showMonitorInfo: function(){
				var me = this;
				var viewid = 'monitor-info-template'
				timer = setInterval(function(){
					me.model($("#" + viewid).data('post'), {}, function(data){
						//模板渲染
						me.render(viewid, data, function(content){
							$("div#monitor-info").html("").html(content)
						});
					});
				}, 3000);
				
			},
			
			model: function(url, data, callback){
				L.ajax({
					type: arguments[3] || 'GET',
					url: url,
					cache: true,
					data: data || {},
					success:function(data){
						callback && callback(data);
					}
				});
			},
		
		    render:function(viewid, data, callback) {
				L.template(function(template){
					var content = template.render(viewid, data);
					typeof callback == 'function'  && callback(content);
				});
			}

	};
	
	index.init();
	
	return index;
	
});