/* Pareto card -- built from frontend/src, do not edit by hand. */
"use strict";(()=>{var O=globalThis,z=O.ShadowRoot&&(O.ShadyCSS===void 0||O.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,W=Symbol(),nt=new WeakMap,C=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==W)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(z&&t===void 0){let i=e!==void 0&&e.length===1;i&&(t=nt.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&nt.set(e,t))}return t}toString(){return this.cssText}},ot=n=>new C(typeof n=="string"?n:n+"",void 0,W),V=(n,...t)=>{let e=n.length===1?n[0]:t.reduce((i,s,o)=>i+(r=>{if(r._$cssResult$===!0)return r.cssText;if(typeof r=="number")return r;throw Error("Value passed to 'css' function must be a 'css' function result: "+r+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+n[o+1],n[0]);return new C(e,n,W)},rt=(n,t)=>{if(z)n.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let i=document.createElement("style"),s=O.litNonce;s!==void 0&&i.setAttribute("nonce",s),i.textContent=e.cssText,n.appendChild(i)}},I=z?n=>n:n=>n instanceof CSSStyleSheet?(t=>{let e="";for(let i of t.cssRules)e+=i.cssText;return ot(e)})(n):n;var{is:Ht,defineProperty:Rt,getOwnPropertyDescriptor:Tt,getOwnPropertyNames:kt,getOwnPropertySymbols:Mt,getPrototypeOf:Nt}=Object,y=globalThis,at=y.trustedTypes,Ut=at?at.emptyScript:"",K=y.reactiveElementPolyfillSupport,P=(n,t)=>n,q={toAttribute(n,t){switch(t){case Boolean:n=n?Ut:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,t){let e=n;switch(t){case Boolean:e=n!==null;break;case Number:e=n===null?null:Number(n);break;case Object:case Array:try{e=JSON.parse(n)}catch{e=null}}return e}},ht=(n,t)=>!Ht(n,t),lt={attribute:!0,type:String,converter:q,reflect:!1,useDefault:!1,hasChanged:ht};Symbol.metadata??(Symbol.metadata=Symbol("metadata")),y.litPropertyMetadata??(y.litPropertyMetadata=new WeakMap);var m=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??(this.l=[])).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=lt){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let i=Symbol(),s=this.getPropertyDescriptor(t,i,e);s!==void 0&&Rt(this.prototype,t,s)}}static getPropertyDescriptor(t,e,i){let{get:s,set:o}=Tt(this.prototype,t)??{get(){return this[e]},set(r){this[e]=r}};return{get:s,set(r){let l=s==null?void 0:s.call(this);o==null||o.call(this,r),this.requestUpdate(t,l,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??lt}static _$Ei(){if(this.hasOwnProperty(P("elementProperties")))return;let t=Nt(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(P("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(P("properties"))){let e=this.properties,i=[...kt(e),...Mt(e)];for(let s of i)this.createProperty(s,e[s])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[i,s]of e)this.elementProperties.set(i,s)}this._$Eh=new Map;for(let[e,i]of this.elementProperties){let s=this._$Eu(e,i);s!==void 0&&this._$Eh.set(s,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let i=new Set(t.flat(1/0).reverse());for(let s of i)e.unshift(I(s))}else t!==void 0&&e.push(I(t));return e}static _$Eu(t,e){let i=e.attribute;return i===!1?void 0:typeof i=="string"?i:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){var t;this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),(t=this.constructor.l)==null||t.forEach(e=>e(this))}addController(t){var e;(this._$EO??(this._$EO=new Set)).add(t),this.renderRoot!==void 0&&this.isConnected&&((e=t.hostConnected)==null||e.call(t))}removeController(t){var e;(e=this._$EO)==null||e.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return rt(t,this.constructor.elementStyles),t}connectedCallback(){var t;this.renderRoot??(this.renderRoot=this.createRenderRoot()),this.enableUpdating(!0),(t=this._$EO)==null||t.forEach(e=>{var i;return(i=e.hostConnected)==null?void 0:i.call(e)})}enableUpdating(t){}disconnectedCallback(){var t;(t=this._$EO)==null||t.forEach(e=>{var i;return(i=e.hostDisconnected)==null?void 0:i.call(e)})}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){var o;let i=this.constructor.elementProperties.get(t),s=this.constructor._$Eu(t,i);if(s!==void 0&&i.reflect===!0){let r=(((o=i.converter)==null?void 0:o.toAttribute)!==void 0?i.converter:q).toAttribute(e,i.type);this._$Em=t,r==null?this.removeAttribute(s):this.setAttribute(s,r),this._$Em=null}}_$AK(t,e){var o,r;let i=this.constructor,s=i._$Eh.get(t);if(s!==void 0&&this._$Em!==s){let l=i.getPropertyOptions(s),a=typeof l.converter=="function"?{fromAttribute:l.converter}:((o=l.converter)==null?void 0:o.fromAttribute)!==void 0?l.converter:q;this._$Em=s;let c=a.fromAttribute(e,l.type);this[s]=c??((r=this._$Ej)==null?void 0:r.get(s))??c,this._$Em=null}}requestUpdate(t,e,i,s=!1,o){var r;if(t!==void 0){let l=this.constructor;if(s===!1&&(o=this[t]),i??(i=l.getPropertyOptions(t)),!((i.hasChanged??ht)(o,e)||i.useDefault&&i.reflect&&o===((r=this._$Ej)==null?void 0:r.get(t))&&!this.hasAttribute(l._$Eu(t,i))))return;this.C(t,e,i)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:s,wrapped:o},r){i&&!(this._$Ej??(this._$Ej=new Map)).has(t)&&(this._$Ej.set(t,r??e??this[t]),o!==!0||r!==void 0)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),s===!0&&this._$Em!==t&&(this._$Eq??(this._$Eq=new Set)).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){var i;if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??(this.renderRoot=this.createRenderRoot()),this._$Ep){for(let[o,r]of this._$Ep)this[o]=r;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[o,r]of s){let{wrapped:l}=r,a=this[o];l!==!0||this._$AL.has(o)||a===void 0||this.C(o,void 0,r,a)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),(i=this._$EO)==null||i.forEach(s=>{var o;return(o=s.hostUpdate)==null?void 0:o.call(s)}),this.update(e)):this._$EM()}catch(s){throw t=!1,this._$EM(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){var e;(e=this._$EO)==null||e.forEach(i=>{var s;return(s=i.hostUpdated)==null?void 0:s.call(i)}),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&(this._$Eq=this._$Eq.forEach(e=>this._$ET(e,this[e]))),this._$EM()}updated(t){}firstUpdated(t){}};m.elementStyles=[],m.shadowRootOptions={mode:"open"},m[P("elementProperties")]=new Map,m[P("finalized")]=new Map,K==null||K({ReactiveElement:m}),(y.reactiveElementVersions??(y.reactiveElementVersions=[])).push("2.1.2");var R=globalThis,dt=n=>n,D=R.trustedTypes,ct=D?D.createPolicy("lit-html",{createHTML:n=>n}):void 0,gt="$lit$",$=`lit$${Math.random().toFixed(9).slice(2)}$`,yt="?"+$,Lt=`<${yt}>`,A=document,T=()=>A.createComment(""),k=n=>n===null||typeof n!="object"&&typeof n!="function",tt=Array.isArray,Ot=n=>tt(n)||typeof(n==null?void 0:n[Symbol.iterator])=="function",F=`[ 	
\f\r]`,H=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,pt=/-->/g,ut=/>/g,v=RegExp(`>|${F}(?:([^\\s"'>=/]+)(${F}*=${F}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),_t=/'/g,ft=/"/g,$t=/^(?:script|style|textarea|title)$/i,et=n=>(t,...e)=>({_$litType$:n,strings:t,values:e}),u=et(1),Ft=et(2),Jt=et(3),w=Symbol.for("lit-noChange"),h=Symbol.for("lit-nothing"),mt=new WeakMap,b=A.createTreeWalker(A,129);function vt(n,t){if(!tt(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return ct!==void 0?ct.createHTML(t):t}var zt=(n,t)=>{let e=n.length-1,i=[],s,o=t===2?"<svg>":t===3?"<math>":"",r=H;for(let l=0;l<e;l++){let a=n[l],c,p,d=-1,f=0;for(;f<a.length&&(r.lastIndex=f,p=r.exec(a),p!==null);)f=r.lastIndex,r===H?p[1]==="!--"?r=pt:p[1]!==void 0?r=ut:p[2]!==void 0?($t.test(p[2])&&(s=RegExp("</"+p[2],"g")),r=v):p[3]!==void 0&&(r=v):r===v?p[0]===">"?(r=s??H,d=-1):p[1]===void 0?d=-2:(d=r.lastIndex-p[2].length,c=p[1],r=p[3]===void 0?v:p[3]==='"'?ft:_t):r===ft||r===_t?r=v:r===pt||r===ut?r=H:(r=v,s=void 0);let g=r===v&&n[l+1].startsWith("/>")?" ":"";o+=r===H?a+Lt:d>=0?(i.push(c),a.slice(0,d)+gt+a.slice(d)+$+g):a+$+(d===-2?l:g)}return[vt(n,o+(n[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),i]},M=class n{constructor({strings:t,_$litType$:e},i){let s;this.parts=[];let o=0,r=0,l=t.length-1,a=this.parts,[c,p]=zt(t,e);if(this.el=n.createElement(c,i),b.currentNode=this.el.content,e===2||e===3){let d=this.el.content.firstChild;d.replaceWith(...d.childNodes)}for(;(s=b.nextNode())!==null&&a.length<l;){if(s.nodeType===1){if(s.hasAttributes())for(let d of s.getAttributeNames())if(d.endsWith(gt)){let f=p[r++],g=s.getAttribute(d).split($),L=/([.?@])?(.*)/.exec(f);a.push({type:1,index:o,name:L[2],strings:g,ctor:L[1]==="."?G:L[1]==="?"?Q:L[1]==="@"?X:x}),s.removeAttribute(d)}else d.startsWith($)&&(a.push({type:6,index:o}),s.removeAttribute(d));if($t.test(s.tagName)){let d=s.textContent.split($),f=d.length-1;if(f>0){s.textContent=D?D.emptyScript:"";for(let g=0;g<f;g++)s.append(d[g],T()),b.nextNode(),a.push({type:2,index:++o});s.append(d[f],T())}}}else if(s.nodeType===8)if(s.data===yt)a.push({type:2,index:o});else{let d=-1;for(;(d=s.data.indexOf($,d+1))!==-1;)a.push({type:7,index:o}),d+=$.length-1}o++}}static createElement(t,e){let i=A.createElement("template");return i.innerHTML=t,i}};function S(n,t,e=n,i){var r,l;if(t===w)return t;let s=i!==void 0?(r=e._$Co)==null?void 0:r[i]:e._$Cl,o=k(t)?void 0:t._$litDirective$;return(s==null?void 0:s.constructor)!==o&&((l=s==null?void 0:s._$AO)==null||l.call(s,!1),o===void 0?s=void 0:(s=new o(n),s._$AT(n,e,i)),i!==void 0?(e._$Co??(e._$Co=[]))[i]=s:e._$Cl=s),s!==void 0&&(t=S(n,s._$AS(n,t.values),s,i)),t}var Z=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:i}=this._$AD,s=((t==null?void 0:t.creationScope)??A).importNode(e,!0);b.currentNode=s;let o=b.nextNode(),r=0,l=0,a=i[0];for(;a!==void 0;){if(r===a.index){let c;a.type===2?c=new N(o,o.nextSibling,this,t):a.type===1?c=new a.ctor(o,a.name,a.strings,this,t):a.type===6&&(c=new Y(o,this,t)),this._$AV.push(c),a=i[++l]}r!==(a==null?void 0:a.index)&&(o=b.nextNode(),r++)}return b.currentNode=A,s}p(t){let e=0;for(let i of this._$AV)i!==void 0&&(i.strings!==void 0?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}},N=class n{get _$AU(){var t;return((t=this._$AM)==null?void 0:t._$AU)??this._$Cv}constructor(t,e,i,s){this.type=2,this._$AH=h,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=s,this._$Cv=(s==null?void 0:s.isConnected)??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&(t==null?void 0:t.nodeType)===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=S(this,t,e),k(t)?t===h||t==null||t===""?(this._$AH!==h&&this._$AR(),this._$AH=h):t!==this._$AH&&t!==w&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):Ot(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==h&&k(this._$AH)?this._$AA.nextSibling.data=t:this.T(A.createTextNode(t)),this._$AH=t}$(t){var o;let{values:e,_$litType$:i}=t,s=typeof i=="number"?this._$AC(t):(i.el===void 0&&(i.el=M.createElement(vt(i.h,i.h[0]),this.options)),i);if(((o=this._$AH)==null?void 0:o._$AD)===s)this._$AH.p(e);else{let r=new Z(s,this),l=r.u(this.options);r.p(e),this.T(l),this._$AH=r}}_$AC(t){let e=mt.get(t.strings);return e===void 0&&mt.set(t.strings,e=new M(t)),e}k(t){tt(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,i,s=0;for(let o of t)s===e.length?e.push(i=new n(this.O(T()),this.O(T()),this,this.options)):i=e[s],i._$AI(o),s++;s<e.length&&(this._$AR(i&&i._$AB.nextSibling,s),e.length=s)}_$AR(t=this._$AA.nextSibling,e){var i;for((i=this._$AP)==null?void 0:i.call(this,!1,!0,e);t!==this._$AB;){let s=dt(t).nextSibling;dt(t).remove(),t=s}}setConnected(t){var e;this._$AM===void 0&&(this._$Cv=t,(e=this._$AP)==null||e.call(this,t))}},x=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,s,o){this.type=1,this._$AH=h,this._$AN=void 0,this.element=t,this.name=e,this._$AM=s,this.options=o,i.length>2||i[0]!==""||i[1]!==""?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=h}_$AI(t,e=this,i,s){let o=this.strings,r=!1;if(o===void 0)t=S(this,t,e,0),r=!k(t)||t!==this._$AH&&t!==w,r&&(this._$AH=t);else{let l=t,a,c;for(t=o[0],a=0;a<o.length-1;a++)c=S(this,l[i+a],e,a),c===w&&(c=this._$AH[a]),r||(r=!k(c)||c!==this._$AH[a]),c===h?t=h:t!==h&&(t+=(c??"")+o[a+1]),this._$AH[a]=c}r&&!s&&this.j(t)}j(t){t===h?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},G=class extends x{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===h?void 0:t}},Q=class extends x{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==h)}},X=class extends x{constructor(t,e,i,s,o){super(t,e,i,s,o),this.type=5}_$AI(t,e=this){if((t=S(this,t,e,0)??h)===w)return;let i=this._$AH,s=t===h&&i!==h||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,o=t!==h&&(i===h||s);s&&this.element.removeEventListener(this.name,this,i),o&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){var e;typeof this._$AH=="function"?this._$AH.call(((e=this.options)==null?void 0:e.host)??this.element,t):this._$AH.handleEvent(t)}},Y=class{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){S(this,t)}};var J=R.litHtmlPolyfillSupport;J==null||J(M,N),(R.litHtmlVersions??(R.litHtmlVersions=[])).push("3.3.3");var bt=(n,t,e)=>{let i=(e==null?void 0:e.renderBefore)??t,s=i._$litPart$;if(s===void 0){let o=(e==null?void 0:e.renderBefore)??null;i._$litPart$=s=new N(t.insertBefore(T(),o),o,void 0,e??{})}return s._$AI(n),s};var E=globalThis,_=class extends m{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){var e;let t=super.createRenderRoot();return(e=this.renderOptions).renderBefore??(e.renderBefore=t.firstChild),t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=bt(e,this.renderRoot,this.renderOptions)}connectedCallback(){var t;super.connectedCallback(),(t=this._$Do)==null||t.setConnected(!0)}disconnectedCallback(){var t;super.disconnectedCallback(),(t=this._$Do)==null||t.setConnected(!1)}render(){return w}},At;_._$litElement$=!0,_.finalized=!0,(At=E.litElementHydrateSupport)==null||At.call(E,{LitElement:_});var it=E.litElementPolyfillSupport;it==null||it({LitElement:_});(E.litElementVersions??(E.litElementVersions=[])).push("4.2.2");var Dt=["top","recent"];function wt(n){if(typeof n!="object"||n===null)throw new Error("pareto-card: configuration is missing");let t=n,e=t.mode===void 0?"top":t.mode;if(typeof e!="string"||!Dt.includes(e))throw new Error(`pareto-card: unknown mode "${String(e)}", expected top or recent`);let i;if(t.columns!==void 0){if(typeof t.columns!="number"||!Number.isInteger(t.columns)||t.columns<1)throw new Error("pareto-card: columns must be a whole number of 1 or more");i=t.columns}if(t.show_title!==void 0&&typeof t.show_title!="boolean")throw new Error("pareto-card: show_title must be true or false");return{type:typeof t.type=="string"?t.type:"custom:pareto-card",mode:e,title:t.title===void 0?void 0:String(t.title),show_title:t.show_title===void 0?!0:t.show_title,columns:i}}function Et(n,t,e=3e4){return n===null?!0:t-n>=e}function St(n){return n&&n>0?`repeat(${n}, minmax(0, 1fr))`:"repeat(auto-fill, minmax(140px, 1fr))"}function xt(n,t){let e=t&&t>0?t:2;return 1+Math.ceil(n/e)}function Ct(n,t){var e;return((e=n==null?void 0:n.states[t])==null?void 0:e.attributes.friendly_name)??t}function Pt(n,t,e,i){if(e.hidden===!0){let s=o=>o.filter(r=>r.entity_id!==t);return{top:s(n.top),recent:s(n.recent),hidden:i.hidden}}if(e.pinned!==void 0){let s=o=>o.map(r=>r.entity_id===t?{...r,pinned:e.pinned}:r);return{top:s(n.top),recent:s(n.recent),hidden:i.hidden}}return{...n,hidden:i.hidden}}function st(n){return typeof n=="object"&&n!==null&&"message"in n?String(n.message):String(n)}var jt={top:"Most used",recent:"Recently used",edit:"Edit list",done:"Done",hide:"Hide from my list",pin:"Pin to the top",unpin:"Remove pin",restore:"Show again",hiddenHeading:"Hidden by me",empty:"Nothing recorded yet.",allHidden:"Everything is hidden. Use edit mode to bring an entry back.",noHelpers:"This Home Assistant frontend provides no card helpers.",mode:"List",title:"Title (empty: named after the list)",show_title:"Show the title",columns:"Columns (empty: fits the width)"},Bt={top:"Meistgenutzt",recent:"Zuletzt benutzt",edit:"Liste bearbeiten",done:"Fertig",hide:"Aus meiner Liste ausblenden",pin:"Nach oben anheften",unpin:"Anheftung l\xF6sen",restore:"Wieder anzeigen",hiddenHeading:"Von mir ausgeblendet",empty:"Noch keine Bedienungen erfasst.",allHidden:"Alles ausgeblendet. Im Bearbeiten-Modus l\xE4sst sich ein Eintrag zur\xFCckholen.",noHelpers:"Dieses Home-Assistant-Frontend stellt keine Card-Helpers bereit.",mode:"Liste",title:"Titel (leer: benannt nach der Liste)",show_title:"Titel anzeigen",columns:"Spalten (leer: passt sich der Breite an)"};function j(n,t){return n!=null&&n.toLowerCase().startsWith("de")?Bt[t]:jt[t]}var Wt=[{name:"mode",selector:{select:{mode:"dropdown",options:[{value:"top",label:"Most used"},{value:"recent",label:"Recently used"}]}}},{name:"show_title",selector:{boolean:{}}},{name:"title",selector:{text:{}}},{name:"columns",selector:{number:{min:1,max:6,mode:"box"}}}],B=class extends _{constructor(){super(...arguments);this._label=e=>{var i,s;return j((s=(i=this.hass)==null?void 0:i.locale)==null?void 0:s.language,e.name)}}setConfig(e){this._config={show_title:!0,...e}}_changed(e){let i={...e.detail.value};i.title===""&&delete i.title,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:i},bubbles:!0,composed:!0}))}render(){return this._config?u`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${Wt}
        .computeLabel=${this._label}
        @value-changed=${this._changed}
      ></ha-form>
    `:h}};B.properties={hass:{attribute:!1},_config:{state:!0}};customElements.get("pareto-card-editor")||customElements.define("pareto-card-editor",B);var U=class extends _{constructor(){super(...arguments);this._editing=!1;this._tiles=new Map;this._loading=!1;this._lastAttempt=null;this._onVisibility=()=>{document.visibilityState==="visible"&&this._load(!1)}}static getStubConfig(){return{mode:"top"}}static getConfigElement(){return document.createElement("pareto-card-editor")}setConfig(e){this._config=wt(e),this._tiles.clear(),this._syncTiles(),this._load(!0)}set hass(e){this._hass=e;for(let i of this._tiles.values())i.hass=e;this._lists===void 0&&this._load(!1)}get hass(){return this._hass}connectedCallback(){super.connectedCallback(),document.addEventListener("visibilitychange",this._onVisibility),this._load(!0)}disconnectedCallback(){super.disconnectedCallback(),document.removeEventListener("visibilitychange",this._onVisibility)}getCardSize(){var e;return xt(this._rows().length,(e=this._config)==null?void 0:e.columns)}_t(e){var i,s;return j((s=(i=this._hass)==null?void 0:i.locale)==null?void 0:s.language,e)}_rows(){return!this._lists||!this._config?[]:this._lists[this._config.mode]}async _ensureHelpers(){if(this._helpers)return;let e=window.loadCardHelpers;if(!e)throw new Error(this._t("noHelpers"));this._helpers=await e()}async _load(e){if(!(!this._hass||!this._config||this._loading)&&!(!e&&!Et(this._lastAttempt,Date.now()))){this._loading=!0;try{await this._ensureHelpers();let i=await this._hass.callWS({type:"pareto/lists"});this._lists=i,this._error=void 0,this._syncTiles()}catch(i){this._error=st(i)}finally{this._lastAttempt=Date.now(),this._loading=!1}}}_syncTiles(){if(!this._helpers||!this._config||!this._lists)return;let e=this._rows(),i=new Set(e.map(s=>s.entity_id));for(let s of[...this._tiles.keys()])i.has(s)||this._tiles.delete(s);for(let s of e){if(this._tiles.has(s.entity_id))continue;let o=this._helpers.createCardElement({type:"tile",entity:s.entity_id});o.hass=this._hass,this._tiles.set(s.entity_id,o)}}_toggleEdit(){this._editing=!this._editing}async _setPref(e,i){if(!(!this._hass||!this._lists))try{let s=await this._hass.callWS({type:"pareto/set_pref",entity_id:e,...i});this._lists=Pt(this._lists,e,i,s),this._error=void 0,this._syncTiles(),i.hidden===!1&&await this._load(!0)}catch(s){this._error=st(s)}}render(){if(!this._config)return h;let e=this._rows();return u`
      <ha-card>
        <div class="head ${this._config.show_title?"":"bare"}">
          ${this._config.show_title?u`<span class="title">${this._config.title??this._t(this._config.mode)}</span>`:h}
          <button
            class="icon"
            title=${this._t(this._editing?"done":"edit")}
            @click=${this._toggleEdit}
          >
            <ha-icon icon=${this._editing?"mdi:check":"mdi:pencil"}></ha-icon>
          </button>
        </div>
        ${this._error?u`<div class="notice error">${this._error}</div>`:h}
        ${e.length?this._grid(e):this._emptyNotice()}
        ${this._editing?this._hiddenSection():h}
      </ha-card>
    `}_grid(e){var i;return u`
      <div class="grid" style="grid-template-columns: ${St((i=this._config)==null?void 0:i.columns)}">
        ${e.map(s=>this._cell(s))}
      </div>
    `}_cell(e){return u`
      <div class="cell ${this._editing?"editing":""}">
        ${this._tiles.get(e.entity_id)}
        ${this._editing?u`
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
    `}_hiddenSection(){var i;let e=((i=this._lists)==null?void 0:i.hidden)??[];return e.length?u`
      <div class="hidden-list">
        <div class="subhead">${this._t("hiddenHeading")}</div>
        ${e.map(s=>u`
            <div class="hidden-row">
              <span class="name">${Ct(this._hass,s)}</span>
              <button
                class="chip"
                title=${this._t("restore")}
                @click=${()=>this._setPref(s,{hidden:!1})}
              >
                <ha-icon icon="mdi:restore"></ha-icon>
              </button>
            </div>
          `)}
      </div>
    `:h}_emptyNotice(){return this._error||!this._lists?h:u`<div class="notice">
      ${this._t(this._lists.hidden.length?"allHidden":"empty")}
    </div>`}};U.properties={_config:{state:!0},_lists:{state:!0},_error:{state:!0},_editing:{state:!0}},U.styles=V`
    ha-card {
      padding: 8px;
    }

    .head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 8px 12px;
    }

    /* Without a title the row exists only to carry the pencil, so it stops
       claiming the height of a heading. */
    .head.bare {
      padding: 0 4px 4px;
      justify-content: flex-end;
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

    /* The pencil is a rarely-used affordance sitting next to a heading, so it
       is deliberately smaller than a normal icon button. */
    button.icon {
      --mdc-icon-size: 18px;
      padding: 2px;
      opacity: 0.7;
    }

    button.icon:hover {
      opacity: 1;
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
  `;customElements.get("pareto-card")||(customElements.define("pareto-card",U),window.customCards=window.customCards??[],window.customCards.push({type:"pareto-card",name:"Pareto",description:"The entities you actually operate, ranked.",preview:!1,documentationURL:"https://github.com/dbackhove/ha-pareto"}));})();
