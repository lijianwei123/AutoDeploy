//文件列表

define(function(require){
	var list = {
			init:function() {
				this.initBind();
			},
			
			initBind:function() {
				var me = this;
				$('.addWPriv, .delWPriv, .forceSync').on('click', function(e){
					var post_url = $(this).data('post');
					seajs.use("plugins/layer/layer.min", function(){
						var index = layer.confirm('亲，你确定吗？', function(){
							me.model(post_url, {}, function(data){
								L.alert('操作成功');
							});
							layer.close(index);
						});
					});
				});
				
				$('.syncStatus').on('click', function(e){
					var post_url = $(this).data('post');
					var $elm = $(this)
					seajs.use("plugins/layer/layer.min", function(){
						me.model(post_url, {}, function(data){
							tips = "";
							if(data) {
								for(var ip in data) {
									tips += ip+ " " + data[ip] + "<br>";
								}
							} else {
								tips = "没有信息";
							}
							layer.tips(tips, $elm , {guide: 0, time: 6});
						});
					});
				});
				
				
				
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
	
	list.init();
	
	return list;
	
});
