(function(w) {
    var $commonjs = $('#commonjsnode'),
    base = $commonjs.attr('base-path'),
    plugins = $commonjs.attr('plugins-path'),
    css = $commonjs.attr('css-path'),
    version = $commonjs.attr('version'),
    host = !$commonjs.attr('host') ? window.location.host : $commonjs.attr('host');

    var Config = {
        alias: {
            'tab': 'plugins/tab/tab',
            'pager': 'plugins/flip-page/flip-page',
            'drop': 'plugins/dropdown/dropdown',
            'art-template': 'plugins/art-template/art-template',
            'xheditor': 'plugins/xheditor/my-xheditor',
            'form': 'plugins/form/form',
            'autoemail': 'plugins/form/email-autocomplete',
            'insertContent': 'plugins/form/insert-content',
            'alimap': 'plugins/map/alimap',
            'datepicker': 'plugins/datepicker/datepicker',
            'timepicker': 'plugins/datepicker/jquery-ui-timepicker-addon',
            'autocomplete': 'plugins/form/autocomplete',
            'fupload': 'plugins/upload/iframe-upload',
            'layer': 'plugins/layer/layer',
            'sso': 'http://f3.v.veimg.cn/sso/js/??sso.js,ve_msg_utf8.js'
            
        },
        base : base,
        paths: {
            'app': base + 'app',
            'plugins': plugins.replace(/\/$/, ''),
            'templates': 'templates',
            'css': css.replace(/\/$/, '')
        },
        charset: 'utf-8',
        map: [
        ['.css', '.css?v=' + version],
        ['.js', '.js?v=' + version]
        ],
        debug: false
    };
    
    seajs.config(Config);
    
    var LAZY = {
        init: function() {
            this.browser();
            //this.mustBeChrome();
        },

        run: function(path, callback) {
            seajs.use(path, callback);
        },

        browser: function() {
            //ie6
            if(!-[1,]) {
            	this.isIe = true;
                if (!window.XMLHttpRequest) {
                    $('html').addClass('ie6');
                    this.isIe6 = true;
                }
            }
        },
        
        mustBeChrome: function(){
            if (window.navigator.userAgent.toLowerCase().indexOf('chrome') == -1) {
                   seajs.use("plugins/layer/layer.min", function(layer){
                        $.layer({
                            closeBtn: false,
                            type : 1,
                            title : false,
                            border : false,
                            area : ['400px','400px'],
                            page: {
                              html : "<div style='margin-left:100px;margin-top:50%'><h3>请使用chrome浏览器</h3></div>"
                            }
                        });
                   });
            }
        },
        
        ajax: function(opts) {
        	var me = this;
            var o = $.extend({}, {
                url: '',
                type: 'get',
                data: {},
                dataType: 'json',
                cache: false,
                success: function() {},
                fail: function(response) {
                	typeof(this.onFail) == 'function' && this.onFail(response);
                	me.alert(response.errMsg);
                }
            }, opts);

            $.ajax({
                url: o.url,
                type: o.type,
                data: o.data,
                dataType: o.dataType,
                cache: o.cache,
                success: function(response) {
                    if (response.status === 1) {
                        o.success(response.data);
                    } else {
                        o.fail(response);
                    }
                }
            });
        },

        alert: function(message) {
          seajs.use("plugins/layer/layer.min", function(layer){
             layer.layer[0].msg(message, 1, -1);
          });
        },

        loading: function(){
          seajs.use("plugins/layer/layer.min", function(layer){
             layer.layer[0].load('努力干活中。。。', 0);
          });
        },
    
        template: function(callback) {
         var me = this;
         seajs.use('art-template', function(template) {
          template.helper('substring', function() {return me.escape(me.substring.apply(me, arguments))});
          template.helper('createUrl', function(){return me.createUrl.apply(me, arguments)});
          template.helper('charCode', me.charCode);

          var dateMap = {'Y': [0, 4], 'y': [2, 2], 'm': [5, 2], 'd': [8, 2], 'H': [11, 2], 'i': [14, 2], 's': [17, 2]};
          template.helper('date', function(str, format) {
           if (typeof str !== 'string' || !str) return '';
           format = format || 'Y-m-d';
           return format.replace(/[a-zA-Z]+/g, function(key) {
            return String.prototype.substr.apply(str, dateMap[key]);
          });
         });

          template.helper('strtotime', function(str) {
            return Math.round(Date.parse(str) / 1000);
          });
          
          template.helper('json_parse', function(){
        	  return JSON.parse.apply({}, arguments);
          });
          template.helper('json_stringify', function(){
        	  return JSON.stringify.apply({}, arguments);
          });
          (typeof(callback) == 'function') && callback(template);
        });
       },

       escape: function (content) {
        return typeof content === 'string'
        ? content.replace(/&(?![\w#]+;)|[<>"']/g, function (s) {
          return {
            "<": "&#60;",
            ">": "&#62;",
            '"': "&#34;",
            "'": "&#39;",
            "&": "&#38;"
          }[s];
        })
        : content;
      },

      createUrl: function(path, params) {
        path = path ? path : '';
        var url = (path.indexOf('http') === 0) ? path : 'http://' + host + (path.indexOf('/') === 0 ? '' : '/') + path;

        if (params) {
          var get = $.param(params);
          if (get) url += (/\?/.test(url) ? "&" : "?") + get;
        }
        return url;
      },
      
      substring: function (str, len, flow) {
  		if ( ! str) return '';
  		str = str.toString();
  	    var newStr = "",
  	    	strLength = str.replace(/[^\x00-\xff]/g, "**").length,
  	    	flow = typeof(flow) == 'undefined' ? '...' : flow;
  	    
  	    if (strLength <= len + (strLength % 2 == 0 ? 2 : 1)) return str;
  	    
  	    for (var i = 0, newLength = 0, singleChar; i < strLength; i++) {
  	        singleChar = str.charAt(i).toString();
  	        if (singleChar.match(/[^\x00-\xff]/g) != null) newLength += 2;
  	        else newLength++;
  	        
  	        if (newLength > len) break;
  	        newStr += singleChar;  
  	    }

  	    if (strLength > len) newStr = $.trim(newStr) + flow;
  	    return newStr;
  	},


      _cache: {},

      cache: function(key, value) {
        if (typeof(value) == 'undefined') return this._cache[key] || null;
        else this._cache[key] = value;
      },

      log: function(errMsg) {
        window.console && window.console.log(errMsg);
      }
};

LAZY.init();

w.L = LAZY;

}(window));