/* Pareto card -- built from frontend/src, do not edit by hand. */
"use strict";(()=>{var N=globalThis,U=N.ShadowRoot&&(N.ShadyCSS===void 0||N.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,z=Symbol(),Y=new WeakMap,S=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==z)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(U&&t===void 0){let i=e!==void 0&&e.length===1;i&&(t=Y.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&Y.set(e,t))}return t}toString(){return this.cssText}},tt=n=>new S(typeof n=="string"?n:n+"",void 0,z),D=(n,...t)=>{let e=n.length===1?n[0]:t.reduce((i,s,r)=>i+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+n[r+1],n[0]);return new S(e,n,z)},et=(n,t)=>{if(U)n.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let i=document.createElement("style"),s=N.litNonce;s!==void 0&&i.setAttribute("nonce",s),i.textContent=e.cssText,n.appendChild(i)}},j=U?n=>n:n=>n instanceof CSSStyleSheet?(t=>{let e="";for(let i of t.cssRules)e+=i.cssText;return tt(e)})(n):n;var{is:Et,defineProperty:St,getOwnPropertyDescriptor:xt,getOwnPropertyNames:Ct,getOwnPropertySymbols:Pt,getPrototypeOf:Ht}=Object,O=globalThis,it=O.trustedTypes,Rt=it?it.emptyScript:"",Tt=O.reactiveElementPolyfillSupport,x=(n,t)=>n,B={toAttribute(n,t){switch(t){case Boolean:n=n?Rt:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,t){let e=n;switch(t){case Boolean:e=n!==null;break;case Number:e=n===null?null:Number(n);break;case Object:case Array:try{e=JSON.parse(n)}catch{e=null}}return e}},nt=(n,t)=>!Et(n,t),st={attribute:!0,type:String,converter:B,reflect:!1,useDefault:!1,hasChanged:nt};Symbol.metadata??=Symbol("metadata"),O.litPropertyMetadata??=new WeakMap;var _=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=st){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let i=Symbol(),s=this.getPropertyDescriptor(t,i,e);s!==void 0&&St(this.prototype,t,s)}}static getPropertyDescriptor(t,e,i){let{get:s,set:r}=xt(this.prototype,t)??{get(){return this[e]},set(o){this[e]=o}};return{get:s,set(o){let d=s?.call(this);r?.call(this,o),this.requestUpdate(t,d,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??st}static _$Ei(){if(this.hasOwnProperty(x("elementProperties")))return;let t=Ht(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(x("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(x("properties"))){let e=this.properties,i=[...Ct(e),...Pt(e)];for(let s of i)this.createProperty(s,e[s])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[i,s]of e)this.elementProperties.set(i,s)}this._$Eh=new Map;for(let[e,i]of this.elementProperties){let s=this._$Eu(e,i);s!==void 0&&this._$Eh.set(s,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let i=new Set(t.flat(1/0).reverse());for(let s of i)e.unshift(j(s))}else t!==void 0&&e.push(j(t));return e}static _$Eu(t,e){let i=e.attribute;return i===!1?void 0:typeof i=="string"?i:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return et(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){let i=this.constructor.elementProperties.get(t),s=this.constructor._$Eu(t,i);if(s!==void 0&&i.reflect===!0){let r=(i.converter?.toAttribute!==void 0?i.converter:B).toAttribute(e,i.type);this._$Em=t,r==null?this.removeAttribute(s):this.setAttribute(s,r),this._$Em=null}}_$AK(t,e){let i=this.constructor,s=i._$Eh.get(t);if(s!==void 0&&this._$Em!==s){let r=i.getPropertyOptions(s),o=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:B;this._$Em=s;let d=o.fromAttribute(e,r.type);this[s]=d??this._$Ej?.get(s)??d,this._$Em=null}}requestUpdate(t,e,i,s=!1,r){if(t!==void 0){let o=this.constructor;if(s===!1&&(r=this[t]),i??=o.getPropertyOptions(t),!((i.hasChanged??nt)(r,e)||i.useDefault&&i.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,i))))return;this.C(t,e,i)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:s,wrapped:r},o){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),r!==!0||o!==void 0)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),s===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[s,r]of this._$Ep)this[s]=r;this._$Ep=void 0}let i=this.constructor.elementProperties;if(i.size>0)for(let[s,r]of i){let{wrapped:o}=r,d=this[s];o!==!0||this._$AL.has(s)||d===void 0||this.C(s,void 0,r,d)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(i=>i.hostUpdate?.()),this.update(e)):this._$EM()}catch(i){throw t=!1,this._$EM(),i}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};_.elementStyles=[],_.shadowRootOptions={mode:"open"},_[x("elementProperties")]=new Map,_[x("finalized")]=new Map,Tt?.({ReactiveElement:_}),(O.reactiveElementVersions??=[]).push("2.1.2");var J=globalThis,rt=n=>n,L=J.trustedTypes,ot=L?L.createPolicy("lit-html",{createHTML:n=>n}):void 0,pt="$lit$",g=`lit$${Math.random().toFixed(9).slice(2)}$`,ut="?"+g,Mt=`<${ut}>`,A=document,P=()=>A.createComment(""),H=n=>n===null||typeof n!="object"&&typeof n!="function",Z=Array.isArray,kt=n=>Z(n)||typeof n?.[Symbol.iterator]=="function",V=`[ 	
\f\r]`,C=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,at=/-->/g,ht=/>/g,y=RegExp(`>|${V}(?:([^\\s"'>=/]+)(${V}*=${V}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),lt=/'/g,dt=/"/g,_t=/^(?:script|style|textarea|title)$/i,G=n=>(t,...e)=>({_$litType$:n,strings:t,values:e}),f=G(1),It=G(2),Ft=G(3),b=Symbol.for("lit-noChange"),h=Symbol.for("lit-nothing"),ct=new WeakMap,v=A.createTreeWalker(A,129);function ft(n,t){if(!Z(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return ot!==void 0?ot.createHTML(t):t}var Nt=(n,t)=>{let e=n.length-1,i=[],s,r=t===2?"<svg>":t===3?"<math>":"",o=C;for(let d=0;d<e;d++){let a=n[d],c,p,l=-1,u=0;for(;u<a.length&&(o.lastIndex=u,p=o.exec(a),p!==null);)u=o.lastIndex,o===C?p[1]==="!--"?o=at:p[1]!==void 0?o=ht:p[2]!==void 0?(_t.test(p[2])&&(s=RegExp("</"+p[2],"g")),o=y):p[3]!==void 0&&(o=y):o===y?p[0]===">"?(o=s??C,l=-1):p[1]===void 0?l=-2:(l=o.lastIndex-p[2].length,c=p[1],o=p[3]===void 0?y:p[3]==='"'?dt:lt):o===dt||o===lt?o=y:o===at||o===ht?o=C:(o=y,s=void 0);let m=o===y&&n[d+1].startsWith("/>")?" ":"";r+=o===C?a+Mt:l>=0?(i.push(c),a.slice(0,l)+pt+a.slice(l)+g+m):a+g+(l===-2?d:m)}return[ft(n,r+(n[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),i]},R=class n{constructor({strings:t,_$litType$:e},i){let s;this.parts=[];let r=0,o=0,d=t.length-1,a=this.parts,[c,p]=Nt(t,e);if(this.el=n.createElement(c,i),v.currentNode=this.el.content,e===2||e===3){let l=this.el.content.firstChild;l.replaceWith(...l.childNodes)}for(;(s=v.nextNode())!==null&&a.length<d;){if(s.nodeType===1){if(s.hasAttributes())for(let l of s.getAttributeNames())if(l.endsWith(pt)){let u=p[o++],m=s.getAttribute(l).split(g),k=/([.?@])?(.*)/.exec(u);a.push({type:1,index:r,name:k[2],strings:m,ctor:k[1]==="."?I:k[1]==="?"?F:k[1]==="@"?K:E}),s.removeAttribute(l)}else l.startsWith(g)&&(a.push({type:6,index:r}),s.removeAttribute(l));if(_t.test(s.tagName)){let l=s.textContent.split(g),u=l.length-1;if(u>0){s.textContent=L?L.emptyScript:"";for(let m=0;m<u;m++)s.append(l[m],P()),v.nextNode(),a.push({type:2,index:++r});s.append(l[u],P())}}}else if(s.nodeType===8)if(s.data===ut)a.push({type:2,index:r});else{let l=-1;for(;(l=s.data.indexOf(g,l+1))!==-1;)a.push({type:7,index:r}),l+=g.length-1}r++}}static createElement(t,e){let i=A.createElement("template");return i.innerHTML=t,i}};function w(n,t,e=n,i){if(t===b)return t;let s=i!==void 0?e._$Co?.[i]:e._$Cl,r=H(t)?void 0:t._$litDirective$;return s?.constructor!==r&&(s?._$AO?.(!1),r===void 0?s=void 0:(s=new r(n),s._$AT(n,e,i)),i!==void 0?(e._$Co??=[])[i]=s:e._$Cl=s),s!==void 0&&(t=w(n,s._$AS(n,t.values),s,i)),t}var W=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:i}=this._$AD,s=(t?.creationScope??A).importNode(e,!0);v.currentNode=s;let r=v.nextNode(),o=0,d=0,a=i[0];for(;a!==void 0;){if(o===a.index){let c;a.type===2?c=new T(r,r.nextSibling,this,t):a.type===1?c=new a.ctor(r,a.name,a.strings,this,t):a.type===6&&(c=new q(r,this,t)),this._$AV.push(c),a=i[++d]}o!==a?.index&&(r=v.nextNode(),o++)}return v.currentNode=A,s}p(t){let e=0;for(let i of this._$AV)i!==void 0&&(i.strings!==void 0?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}},T=class n{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,s){this.type=2,this._$AH=h,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=w(this,t,e),H(t)?t===h||t==null||t===""?(this._$AH!==h&&this._$AR(),this._$AH=h):t!==this._$AH&&t!==b&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):kt(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==h&&H(this._$AH)?this._$AA.nextSibling.data=t:this.T(A.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:i}=t,s=typeof i=="number"?this._$AC(t):(i.el===void 0&&(i.el=R.createElement(ft(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(e);else{let r=new W(s,this),o=r.u(this.options);r.p(e),this.T(o),this._$AH=r}}_$AC(t){let e=ct.get(t.strings);return e===void 0&&ct.set(t.strings,e=new R(t)),e}k(t){Z(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,i,s=0;for(let r of t)s===e.length?e.push(i=new n(this.O(P()),this.O(P()),this,this.options)):i=e[s],i._$AI(r),s++;s<e.length&&(this._$AR(i&&i._$AB.nextSibling,s),e.length=s)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let i=rt(t).nextSibling;rt(t).remove(),t=i}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},E=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,s,r){this.type=1,this._$AH=h,this._$AN=void 0,this.element=t,this.name=e,this._$AM=s,this.options=r,i.length>2||i[0]!==""||i[1]!==""?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=h}_$AI(t,e=this,i,s){let r=this.strings,o=!1;if(r===void 0)t=w(this,t,e,0),o=!H(t)||t!==this._$AH&&t!==b,o&&(this._$AH=t);else{let d=t,a,c;for(t=r[0],a=0;a<r.length-1;a++)c=w(this,d[i+a],e,a),c===b&&(c=this._$AH[a]),o||=!H(c)||c!==this._$AH[a],c===h?t=h:t!==h&&(t+=(c??"")+r[a+1]),this._$AH[a]=c}o&&!s&&this.j(t)}j(t){t===h?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},I=class extends E{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===h?void 0:t}},F=class extends E{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==h)}},K=class extends E{constructor(t,e,i,s,r){super(t,e,i,s,r),this.type=5}_$AI(t,e=this){if((t=w(this,t,e,0)??h)===b)return;let i=this._$AH,s=t===h&&i!==h||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,r=t!==h&&(i===h||s);s&&this.element.removeEventListener(this.name,this,i),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},q=class{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){w(this,t)}};var Ut=J.litHtmlPolyfillSupport;Ut?.(R,T),(J.litHtmlVersions??=[]).push("3.3.3");var mt=(n,t,e)=>{let i=e?.renderBefore??t,s=i._$litPart$;if(s===void 0){let r=e?.renderBefore??null;i._$litPart$=s=new T(t.insertBefore(P(),r),r,void 0,e??{})}return s._$AI(n),s};var Q=globalThis,$=class extends _{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=mt(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return b}};$._$litElement$=!0,$.finalized=!0,Q.litElementHydrateSupport?.({LitElement:$});var Ot=Q.litElementPolyfillSupport;Ot?.({LitElement:$});(Q.litElementVersions??=[]).push("4.2.2");var Lt=["top","recent"];function gt(n){if(typeof n!="object"||n===null)throw new Error("pareto-card: configuration is missing");let t=n,e=t.mode===void 0?"top":t.mode;if(typeof e!="string"||!Lt.includes(e))throw new Error(`pareto-card: unknown mode "${String(e)}", expected top or recent`);let i;if(t.columns!==void 0){if(typeof t.columns!="number"||!Number.isInteger(t.columns)||t.columns<1)throw new Error("pareto-card: columns must be a whole number of 1 or more");i=t.columns}return{type:typeof t.type=="string"?t.type:"custom:pareto-card",mode:e,title:t.title===void 0?void 0:String(t.title),columns:i}}function $t(n,t,e=3e4){return n===null?!0:t-n>=e}function yt(n){return n&&n>0?`repeat(${n}, minmax(0, 1fr))`:"repeat(auto-fill, minmax(140px, 1fr))"}function vt(n,t){let e=t&&t>0?t:2;return 1+Math.ceil(n/e)}function At(n,t){return n?.states[t]?.attributes.friendly_name??t}function bt(n,t,e,i){if(e.hidden===!0){let s=r=>r.filter(o=>o.entity_id!==t);return{top:s(n.top),recent:s(n.recent),hidden:i.hidden}}if(e.pinned!==void 0){let s=r=>r.map(o=>o.entity_id===t?{...o,pinned:e.pinned}:o);return{top:s(n.top),recent:s(n.recent),hidden:i.hidden}}return{...n,hidden:i.hidden}}function X(n){return typeof n=="object"&&n!==null&&"message"in n?String(n.message):String(n)}var zt={top:"Most used",recent:"Recently used",edit:"Edit list",done:"Done",hide:"Hide from my list",pin:"Pin to the top",unpin:"Remove pin",restore:"Show again",hiddenHeading:"Hidden by me",empty:"Nothing recorded yet.",allHidden:"Everything is hidden. Use edit mode to bring an entry back.",noHelpers:"This Home Assistant frontend provides no card helpers."},Dt={top:"Meistgenutzt",recent:"Zuletzt benutzt",edit:"Liste bearbeiten",done:"Fertig",hide:"Aus meiner Liste ausblenden",pin:"Nach oben anheften",unpin:"Anheftung l\xF6sen",restore:"Wieder anzeigen",hiddenHeading:"Von mir ausgeblendet",empty:"Noch keine Bedienungen erfasst.",allHidden:"Alles ausgeblendet. Im Bearbeiten-Modus l\xE4sst sich ein Eintrag zur\xFCckholen.",noHelpers:"Dieses Home-Assistant-Frontend stellt keine Card-Helpers bereit."};function wt(n,t){return n?.toLowerCase().startsWith("de")?Dt[t]:zt[t]}var M=class extends ${constructor(){super(...arguments);this._editing=!1;this._tiles=new Map;this._lastFetch=null;this._onVisibility=()=>{document.visibilityState==="visible"&&this._load(!1)}}static getStubConfig(){return{mode:"top"}}setConfig(e){this._config=gt(e),this._tiles.clear(),this._syncTiles(),this._load(!0)}set hass(e){this._hass=e;for(let i of this._tiles.values())i.hass=e;this._lists===void 0&&this._load(!0)}get hass(){return this._hass}connectedCallback(){super.connectedCallback(),document.addEventListener("visibilitychange",this._onVisibility),this._load(!0)}disconnectedCallback(){super.disconnectedCallback(),document.removeEventListener("visibilitychange",this._onVisibility)}getCardSize(){return vt(this._rows().length,this._config?.columns)}_t(e){return wt(this._hass?.locale?.language,e)}_rows(){return!this._lists||!this._config?[]:this._lists[this._config.mode]}async _ensureHelpers(){if(this._helpers)return;let e=window.loadCardHelpers;if(!e)throw new Error(this._t("noHelpers"));this._helpers=await e()}async _load(e){if(!(!this._hass||!this._config)&&!(!e&&!$t(this._lastFetch,Date.now())))try{await this._ensureHelpers();let i=await this._hass.callWS({type:"pareto/lists"});this._lastFetch=Date.now(),this._lists=i,this._error=void 0,this._syncTiles()}catch(i){this._error=X(i)}}_syncTiles(){if(!this._helpers||!this._config||!this._lists)return;let e=this._rows(),i=new Set(e.map(s=>s.entity_id));for(let s of[...this._tiles.keys()])i.has(s)||this._tiles.delete(s);for(let s of e){if(this._tiles.has(s.entity_id))continue;let r=this._helpers.createCardElement({type:"tile",entity:s.entity_id});r.hass=this._hass,this._tiles.set(s.entity_id,r)}}_toggleEdit(){this._editing=!this._editing}async _setPref(e,i){if(!(!this._hass||!this._lists))try{let s=await this._hass.callWS({type:"pareto/set_pref",entity_id:e,...i});this._lists=bt(this._lists,e,i,s),this._error=void 0,this._syncTiles(),i.hidden===!1&&await this._load(!0)}catch(s){this._error=X(s)}}render(){if(!this._config)return h;let e=this._rows();return f`
      <ha-card>
        <div class="head">
          <span class="title">${this._config.title??this._t(this._config.mode)}</span>
          <button
            class="icon"
            title=${this._t(this._editing?"done":"edit")}
            @click=${this._toggleEdit}
          >
            <ha-icon icon=${this._editing?"mdi:check":"mdi:pencil"}></ha-icon>
          </button>
        </div>
        ${this._error?f`<div class="notice error">${this._error}</div>`:h}
        ${e.length?this._grid(e):this._emptyNotice()}
        ${this._editing?this._hiddenSection():h}
      </ha-card>
    `}_grid(e){return f`
      <div class="grid" style="grid-template-columns: ${yt(this._config?.columns)}">
        ${e.map(i=>this._cell(i))}
      </div>
    `}_cell(e){return f`
      <div class="cell ${this._editing?"editing":""}">
        ${this._tiles.get(e.entity_id)}
        ${this._editing?f`
              <div class="overlay">
                <button
                  class="chip"
                  title=${this._t("hide")}
                  @click=${()=>this._setPref(e.entity_id,{hidden:!0})}
                >
                  <ha-icon icon="mdi:close"></ha-icon>
                </button>
                <button
                  class="chip ${e.pinned?"on":""}"
                  title=${this._t(e.pinned?"unpin":"pin")}
                  @click=${()=>this._setPref(e.entity_id,{pinned:!e.pinned})}
                >
                  <ha-icon icon="mdi:pin"></ha-icon>
                </button>
              </div>
            `:h}
      </div>
    `}_hiddenSection(){let e=this._lists?.hidden??[];return e.length?f`
      <div class="hidden-list">
        <div class="subhead">${this._t("hiddenHeading")}</div>
        ${e.map(i=>f`
            <div class="hidden-row">
              <span class="name">${At(this._hass,i)}</span>
              <button
                class="chip"
                title=${this._t("restore")}
                @click=${()=>this._setPref(i,{hidden:!1})}
              >
                <ha-icon icon="mdi:restore"></ha-icon>
              </button>
            </div>
          `)}
      </div>
    `:h}_emptyNotice(){return this._error||!this._lists?h:f`<div class="notice">
      ${this._t(this._lists.hidden.length?"allHidden":"empty")}
    </div>`}};M.properties={_config:{state:!0},_lists:{state:!0},_error:{state:!0},_editing:{state:!0}},M.styles=D`
    ha-card {
      padding: 8px;
    }

    .head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 8px 12px;
    }

    .title {
      font-size: var(--ha-card-header-font-size, 24px);
      font-weight: 400;
      color: var(--ha-card-header-color, var(--primary-text-color));
    }

    button.icon,
    button.chip {
      background: none;
      border: none;
      cursor: pointer;
      color: var(--secondary-text-color);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 4px;
      border-radius: 50%;
    }

    button.icon:hover,
    button.chip:hover {
      color: var(--primary-text-color);
    }

    .grid {
      display: grid;
      gap: 8px;
    }

    .cell {
      position: relative;
    }

    /* In edit mode the tiles are decoration: a tap must tidy the list, not
       switch the light it happens to land on. */
    .cell.editing > *:not(.overlay) {
      pointer-events: none;
      opacity: 0.55;
    }

    .overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      padding: 4px;
    }

    .overlay .chip {
      background: var(--card-background-color);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }

    .overlay .chip.on {
      color: var(--primary-color);
    }

    .hidden-list {
      margin-top: 12px;
      border-top: 1px solid var(--divider-color);
      padding-top: 8px;
    }

    .subhead {
      font-size: 0.9em;
      color: var(--secondary-text-color);
      padding: 0 8px 4px;
    }

    .hidden-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 2px 8px;
    }

    .hidden-row .name {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .notice {
      padding: 8px 16px 16px;
      color: var(--secondary-text-color);
    }

    .notice.error {
      color: var(--error-color, #db4437);
    }
  `;customElements.get("pareto-card")||(customElements.define("pareto-card",M),window.customCards=window.customCards??[],window.customCards.push({type:"pareto-card",name:"Pareto",description:"The entities you actually operate, ranked.",preview:!1,documentationURL:"https://github.com/dbackhove/ha-pareto"}));})();
