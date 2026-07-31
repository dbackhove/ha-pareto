/* Pareto card -- built from frontend/src, do not edit by hand. */
"use strict";(()=>{var N=globalThis,U=N.ShadowRoot&&(N.ShadyCSS===void 0||N.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,j=Symbol(),et=new WeakMap,S=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==j)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(U&&t===void 0){let i=e!==void 0&&e.length===1;i&&(t=et.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&et.set(e,t))}return t}toString(){return this.cssText}},it=n=>new S(typeof n=="string"?n:n+"",void 0,j),B=(n,...t)=>{let e=n.length===1?n[0]:t.reduce((i,s,o)=>i+(r=>{if(r._$cssResult$===!0)return r.cssText;if(typeof r=="number")return r;throw Error("Value passed to 'css' function must be a 'css' function result: "+r+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+n[o+1],n[0]);return new S(e,n,j)},st=(n,t)=>{if(U)n.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let i=document.createElement("style"),s=N.litNonce;s!==void 0&&i.setAttribute("nonce",s),i.textContent=e.cssText,n.appendChild(i)}},W=U?n=>n:n=>n instanceof CSSStyleSheet?(t=>{let e="";for(let i of t.cssRules)e+=i.cssText;return it(e)})(n):n;var{is:St,defineProperty:xt,getOwnPropertyDescriptor:Ct,getOwnPropertyNames:Pt,getOwnPropertySymbols:Ht,getPrototypeOf:Rt}=Object,L=globalThis,nt=L.trustedTypes,Tt=nt?nt.emptyScript:"",kt=L.reactiveElementPolyfillSupport,x=(n,t)=>n,V={toAttribute(n,t){switch(t){case Boolean:n=n?Tt:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,t){let e=n;switch(t){case Boolean:e=n!==null;break;case Number:e=n===null?null:Number(n);break;case Object:case Array:try{e=JSON.parse(n)}catch{e=null}}return e}},rt=(n,t)=>!St(n,t),ot={attribute:!0,type:String,converter:V,reflect:!1,useDefault:!1,hasChanged:rt};Symbol.metadata??=Symbol("metadata"),L.litPropertyMetadata??=new WeakMap;var m=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=ot){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let i=Symbol(),s=this.getPropertyDescriptor(t,i,e);s!==void 0&&xt(this.prototype,t,s)}}static getPropertyDescriptor(t,e,i){let{get:s,set:o}=Ct(this.prototype,t)??{get(){return this[e]},set(r){this[e]=r}};return{get:s,set(r){let d=s?.call(this);o?.call(this,r),this.requestUpdate(t,d,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??ot}static _$Ei(){if(this.hasOwnProperty(x("elementProperties")))return;let t=Rt(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(x("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(x("properties"))){let e=this.properties,i=[...Pt(e),...Ht(e)];for(let s of i)this.createProperty(s,e[s])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[i,s]of e)this.elementProperties.set(i,s)}this._$Eh=new Map;for(let[e,i]of this.elementProperties){let s=this._$Eu(e,i);s!==void 0&&this._$Eh.set(s,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let i=new Set(t.flat(1/0).reverse());for(let s of i)e.unshift(W(s))}else t!==void 0&&e.push(W(t));return e}static _$Eu(t,e){let i=e.attribute;return i===!1?void 0:typeof i=="string"?i:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return st(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){let i=this.constructor.elementProperties.get(t),s=this.constructor._$Eu(t,i);if(s!==void 0&&i.reflect===!0){let o=(i.converter?.toAttribute!==void 0?i.converter:V).toAttribute(e,i.type);this._$Em=t,o==null?this.removeAttribute(s):this.setAttribute(s,o),this._$Em=null}}_$AK(t,e){let i=this.constructor,s=i._$Eh.get(t);if(s!==void 0&&this._$Em!==s){let o=i.getPropertyOptions(s),r=typeof o.converter=="function"?{fromAttribute:o.converter}:o.converter?.fromAttribute!==void 0?o.converter:V;this._$Em=s;let d=r.fromAttribute(e,o.type);this[s]=d??this._$Ej?.get(s)??d,this._$Em=null}}requestUpdate(t,e,i,s=!1,o){if(t!==void 0){let r=this.constructor;if(s===!1&&(o=this[t]),i??=r.getPropertyOptions(t),!((i.hasChanged??rt)(o,e)||i.useDefault&&i.reflect&&o===this._$Ej?.get(t)&&!this.hasAttribute(r._$Eu(t,i))))return;this.C(t,e,i)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:s,wrapped:o},r){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,r??e??this[t]),o!==!0||r!==void 0)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),s===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[s,o]of this._$Ep)this[s]=o;this._$Ep=void 0}let i=this.constructor.elementProperties;if(i.size>0)for(let[s,o]of i){let{wrapped:r}=o,d=this[s];r!==!0||this._$AL.has(s)||d===void 0||this.C(s,void 0,o,d)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(i=>i.hostUpdate?.()),this.update(e)):this._$EM()}catch(i){throw t=!1,this._$EM(),i}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};m.elementStyles=[],m.shadowRootOptions={mode:"open"},m[x("elementProperties")]=new Map,m[x("finalized")]=new Map,kt?.({ReactiveElement:m}),(L.reactiveElementVersions??=[]).push("2.1.2");var G=globalThis,at=n=>n,O=G.trustedTypes,lt=O?O.createPolicy("lit-html",{createHTML:n=>n}):void 0,_t="$lit$",y=`lit$${Math.random().toFixed(9).slice(2)}$`,ft="?"+y,Mt=`<${ft}>`,b=document,P=()=>b.createComment(""),H=n=>n===null||typeof n!="object"&&typeof n!="function",Q=Array.isArray,Nt=n=>Q(n)||typeof n?.[Symbol.iterator]=="function",I=`[ 	
\f\r]`,C=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,ht=/-->/g,dt=/>/g,$=RegExp(`>|${I}(?:([^\\s"'>=/]+)(${I}*=${I}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),ct=/'/g,pt=/"/g,mt=/^(?:script|style|textarea|title)$/i,X=n=>(t,...e)=>({_$litType$:n,strings:t,values:e}),u=X(1),qt=X(2),Ft=X(3),A=Symbol.for("lit-noChange"),l=Symbol.for("lit-nothing"),ut=new WeakMap,v=b.createTreeWalker(b,129);function gt(n,t){if(!Q(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return lt!==void 0?lt.createHTML(t):t}var Ut=(n,t)=>{let e=n.length-1,i=[],s,o=t===2?"<svg>":t===3?"<math>":"",r=C;for(let d=0;d<e;d++){let a=n[d],c,p,h=-1,f=0;for(;f<a.length&&(r.lastIndex=f,p=r.exec(a),p!==null);)f=r.lastIndex,r===C?p[1]==="!--"?r=ht:p[1]!==void 0?r=dt:p[2]!==void 0?(mt.test(p[2])&&(s=RegExp("</"+p[2],"g")),r=$):p[3]!==void 0&&(r=$):r===$?p[0]===">"?(r=s??C,h=-1):p[1]===void 0?h=-2:(h=r.lastIndex-p[2].length,c=p[1],r=p[3]===void 0?$:p[3]==='"'?pt:ct):r===pt||r===ct?r=$:r===ht||r===dt?r=C:(r=$,s=void 0);let g=r===$&&n[d+1].startsWith("/>")?" ":"";o+=r===C?a+Mt:h>=0?(i.push(c),a.slice(0,h)+_t+a.slice(h)+y+g):a+y+(h===-2?d:g)}return[gt(n,o+(n[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),i]},R=class n{constructor({strings:t,_$litType$:e},i){let s;this.parts=[];let o=0,r=0,d=t.length-1,a=this.parts,[c,p]=Ut(t,e);if(this.el=n.createElement(c,i),v.currentNode=this.el.content,e===2||e===3){let h=this.el.content.firstChild;h.replaceWith(...h.childNodes)}for(;(s=v.nextNode())!==null&&a.length<d;){if(s.nodeType===1){if(s.hasAttributes())for(let h of s.getAttributeNames())if(h.endsWith(_t)){let f=p[r++],g=s.getAttribute(h).split(y),M=/([.?@])?(.*)/.exec(f);a.push({type:1,index:o,name:M[2],strings:g,ctor:M[1]==="."?q:M[1]==="?"?F:M[1]==="@"?J:E}),s.removeAttribute(h)}else h.startsWith(y)&&(a.push({type:6,index:o}),s.removeAttribute(h));if(mt.test(s.tagName)){let h=s.textContent.split(y),f=h.length-1;if(f>0){s.textContent=O?O.emptyScript:"";for(let g=0;g<f;g++)s.append(h[g],P()),v.nextNode(),a.push({type:2,index:++o});s.append(h[f],P())}}}else if(s.nodeType===8)if(s.data===ft)a.push({type:2,index:o});else{let h=-1;for(;(h=s.data.indexOf(y,h+1))!==-1;)a.push({type:7,index:o}),h+=y.length-1}o++}}static createElement(t,e){let i=b.createElement("template");return i.innerHTML=t,i}};function w(n,t,e=n,i){if(t===A)return t;let s=i!==void 0?e._$Co?.[i]:e._$Cl,o=H(t)?void 0:t._$litDirective$;return s?.constructor!==o&&(s?._$AO?.(!1),o===void 0?s=void 0:(s=new o(n),s._$AT(n,e,i)),i!==void 0?(e._$Co??=[])[i]=s:e._$Cl=s),s!==void 0&&(t=w(n,s._$AS(n,t.values),s,i)),t}var K=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:i}=this._$AD,s=(t?.creationScope??b).importNode(e,!0);v.currentNode=s;let o=v.nextNode(),r=0,d=0,a=i[0];for(;a!==void 0;){if(r===a.index){let c;a.type===2?c=new T(o,o.nextSibling,this,t):a.type===1?c=new a.ctor(o,a.name,a.strings,this,t):a.type===6&&(c=new Z(o,this,t)),this._$AV.push(c),a=i[++d]}r!==a?.index&&(o=v.nextNode(),r++)}return v.currentNode=b,s}p(t){let e=0;for(let i of this._$AV)i!==void 0&&(i.strings!==void 0?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}},T=class n{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,s){this.type=2,this._$AH=l,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=w(this,t,e),H(t)?t===l||t==null||t===""?(this._$AH!==l&&this._$AR(),this._$AH=l):t!==this._$AH&&t!==A&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):Nt(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==l&&H(this._$AH)?this._$AA.nextSibling.data=t:this.T(b.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:i}=t,s=typeof i=="number"?this._$AC(t):(i.el===void 0&&(i.el=R.createElement(gt(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(e);else{let o=new K(s,this),r=o.u(this.options);o.p(e),this.T(r),this._$AH=o}}_$AC(t){let e=ut.get(t.strings);return e===void 0&&ut.set(t.strings,e=new R(t)),e}k(t){Q(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,i,s=0;for(let o of t)s===e.length?e.push(i=new n(this.O(P()),this.O(P()),this,this.options)):i=e[s],i._$AI(o),s++;s<e.length&&(this._$AR(i&&i._$AB.nextSibling,s),e.length=s)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let i=at(t).nextSibling;at(t).remove(),t=i}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},E=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,s,o){this.type=1,this._$AH=l,this._$AN=void 0,this.element=t,this.name=e,this._$AM=s,this.options=o,i.length>2||i[0]!==""||i[1]!==""?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=l}_$AI(t,e=this,i,s){let o=this.strings,r=!1;if(o===void 0)t=w(this,t,e,0),r=!H(t)||t!==this._$AH&&t!==A,r&&(this._$AH=t);else{let d=t,a,c;for(t=o[0],a=0;a<o.length-1;a++)c=w(this,d[i+a],e,a),c===A&&(c=this._$AH[a]),r||=!H(c)||c!==this._$AH[a],c===l?t=l:t!==l&&(t+=(c??"")+o[a+1]),this._$AH[a]=c}r&&!s&&this.j(t)}j(t){t===l?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},q=class extends E{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===l?void 0:t}},F=class extends E{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==l)}},J=class extends E{constructor(t,e,i,s,o){super(t,e,i,s,o),this.type=5}_$AI(t,e=this){if((t=w(this,t,e,0)??l)===A)return;let i=this._$AH,s=t===l&&i!==l||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,o=t!==l&&(i===l||s);s&&this.element.removeEventListener(this.name,this,i),o&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},Z=class{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){w(this,t)}};var Lt=G.litHtmlPolyfillSupport;Lt?.(R,T),(G.litHtmlVersions??=[]).push("3.3.3");var yt=(n,t,e)=>{let i=e?.renderBefore??t,s=i._$litPart$;if(s===void 0){let o=e?.renderBefore??null;i._$litPart$=s=new T(t.insertBefore(P(),o),o,void 0,e??{})}return s._$AI(n),s};var Y=globalThis,_=class extends m{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=yt(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return A}};_._$litElement$=!0,_.finalized=!0,Y.litElementHydrateSupport?.({LitElement:_});var Ot=Y.litElementPolyfillSupport;Ot?.({LitElement:_});(Y.litElementVersions??=[]).push("4.2.2");var zt=["top","recent"];function $t(n){if(typeof n!="object"||n===null)throw new Error("pareto-card: configuration is missing");let t=n,e=t.mode===void 0?"top":t.mode;if(typeof e!="string"||!zt.includes(e))throw new Error(`pareto-card: unknown mode "${String(e)}", expected top or recent`);let i;if(t.columns!==void 0){if(typeof t.columns!="number"||!Number.isInteger(t.columns)||t.columns<1)throw new Error("pareto-card: columns must be a whole number of 1 or more");i=t.columns}if(t.show_title!==void 0&&typeof t.show_title!="boolean")throw new Error("pareto-card: show_title must be true or false");return{type:typeof t.type=="string"?t.type:"custom:pareto-card",mode:e,title:t.title===void 0?void 0:String(t.title),show_title:t.show_title===void 0?!0:t.show_title,columns:i}}function vt(n,t,e=3e4){return n===null?!0:t-n>=e}function bt(n){return n&&n>0?`repeat(${n}, minmax(0, 1fr))`:"repeat(auto-fill, minmax(140px, 1fr))"}function At(n,t){let e=t&&t>0?t:2;return 1+Math.ceil(n/e)}function wt(n,t){return n?.states[t]?.attributes.friendly_name??t}function Et(n,t,e,i){if(e.hidden===!0){let s=o=>o.filter(r=>r.entity_id!==t);return{top:s(n.top),recent:s(n.recent),hidden:i.hidden}}if(e.pinned!==void 0){let s=o=>o.map(r=>r.entity_id===t?{...r,pinned:e.pinned}:r);return{top:s(n.top),recent:s(n.recent),hidden:i.hidden}}return{...n,hidden:i.hidden}}function tt(n){return typeof n=="object"&&n!==null&&"message"in n?String(n.message):String(n)}var Dt={top:"Most used",recent:"Recently used",edit:"Edit list",done:"Done",hide:"Hide from my list",pin:"Pin to the top",unpin:"Remove pin",restore:"Show again",hiddenHeading:"Hidden by me",empty:"Nothing recorded yet.",allHidden:"Everything is hidden. Use edit mode to bring an entry back.",noHelpers:"This Home Assistant frontend provides no card helpers.",mode:"List",title:"Title (empty: named after the list)",show_title:"Show the title",columns:"Columns (empty: fits the width)"},jt={top:"Meistgenutzt",recent:"Zuletzt benutzt",edit:"Liste bearbeiten",done:"Fertig",hide:"Aus meiner Liste ausblenden",pin:"Nach oben anheften",unpin:"Anheftung l\xF6sen",restore:"Wieder anzeigen",hiddenHeading:"Von mir ausgeblendet",empty:"Noch keine Bedienungen erfasst.",allHidden:"Alles ausgeblendet. Im Bearbeiten-Modus l\xE4sst sich ein Eintrag zur\xFCckholen.",noHelpers:"Dieses Home-Assistant-Frontend stellt keine Card-Helpers bereit.",mode:"Liste",title:"Titel (leer: benannt nach der Liste)",show_title:"Titel anzeigen",columns:"Spalten (leer: passt sich der Breite an)"};function z(n,t){return n?.toLowerCase().startsWith("de")?jt[t]:Dt[t]}var Bt=[{name:"mode",selector:{select:{mode:"dropdown",options:[{value:"top",label:"Most used"},{value:"recent",label:"Recently used"}]}}},{name:"show_title",selector:{boolean:{}}},{name:"title",selector:{text:{}}},{name:"columns",selector:{number:{min:1,max:6,mode:"box"}}}],D=class extends _{constructor(){super(...arguments);this._label=e=>z(this.hass?.locale?.language,e.name)}setConfig(e){this._config={show_title:!0,...e}}_changed(e){let i={...e.detail.value};i.title===""&&delete i.title,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:i},bubbles:!0,composed:!0}))}render(){return this._config?u`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${Bt}
        .computeLabel=${this._label}
        @value-changed=${this._changed}
      ></ha-form>
    `:l}};D.properties={hass:{attribute:!1},_config:{state:!0}};customElements.get("pareto-card-editor")||customElements.define("pareto-card-editor",D);var k=class extends _{constructor(){super(...arguments);this._editing=!1;this._tiles=new Map;this._loading=!1;this._lastAttempt=null;this._onVisibility=()=>{document.visibilityState==="visible"&&this._load(!1)}}static getStubConfig(){return{mode:"top"}}static getConfigElement(){return document.createElement("pareto-card-editor")}setConfig(e){this._config=$t(e),this._tiles.clear(),this._syncTiles(),this._load(!0)}set hass(e){this._hass=e;for(let i of this._tiles.values())i.hass=e;this._lists===void 0&&this._load(!1)}get hass(){return this._hass}connectedCallback(){super.connectedCallback(),document.addEventListener("visibilitychange",this._onVisibility),this._load(!0)}disconnectedCallback(){super.disconnectedCallback(),document.removeEventListener("visibilitychange",this._onVisibility)}getCardSize(){return At(this._rows().length,this._config?.columns)}_t(e){return z(this._hass?.locale?.language,e)}_rows(){return!this._lists||!this._config?[]:this._lists[this._config.mode]}async _ensureHelpers(){if(this._helpers)return;let e=window.loadCardHelpers;if(!e)throw new Error(this._t("noHelpers"));this._helpers=await e()}async _load(e){if(!(!this._hass||!this._config||this._loading)&&!(!e&&!vt(this._lastAttempt,Date.now()))){this._loading=!0;try{await this._ensureHelpers();let i=await this._hass.callWS({type:"pareto/lists"});this._lists=i,this._error=void 0,this._syncTiles()}catch(i){this._error=tt(i)}finally{this._lastAttempt=Date.now(),this._loading=!1}}}_syncTiles(){if(!this._helpers||!this._config||!this._lists)return;let e=this._rows(),i=new Set(e.map(s=>s.entity_id));for(let s of[...this._tiles.keys()])i.has(s)||this._tiles.delete(s);for(let s of e){if(this._tiles.has(s.entity_id))continue;let o=this._helpers.createCardElement({type:"tile",entity:s.entity_id});o.hass=this._hass,this._tiles.set(s.entity_id,o)}}_toggleEdit(){this._editing=!this._editing}async _setPref(e,i){if(!(!this._hass||!this._lists))try{let s=await this._hass.callWS({type:"pareto/set_pref",entity_id:e,...i});this._lists=Et(this._lists,e,i,s),this._error=void 0,this._syncTiles(),i.hidden===!1&&await this._load(!0)}catch(s){this._error=tt(s)}}render(){if(!this._config)return l;let e=this._rows();return u`
      <ha-card>
        <div class="head ${this._config.show_title?"":"bare"}">
          ${this._config.show_title?u`<span class="title">${this._config.title??this._t(this._config.mode)}</span>`:l}
          <button
            class="icon"
            title=${this._t(this._editing?"done":"edit")}
            @click=${this._toggleEdit}
          >
            <ha-icon icon=${this._editing?"mdi:check":"mdi:pencil"}></ha-icon>
          </button>
        </div>
        ${this._error?u`<div class="notice error">${this._error}</div>`:l}
        ${e.length?this._grid(e):this._emptyNotice()}
        ${this._editing?this._hiddenSection():l}
      </ha-card>
    `}_grid(e){return u`
      <div class="grid" style="grid-template-columns: ${bt(this._config?.columns)}">
        ${e.map(i=>this._cell(i))}
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
            `:l}
      </div>
    `}_hiddenSection(){let e=this._lists?.hidden??[];return e.length?u`
      <div class="hidden-list">
        <div class="subhead">${this._t("hiddenHeading")}</div>
        ${e.map(i=>u`
            <div class="hidden-row">
              <span class="name">${wt(this._hass,i)}</span>
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
    `:l}_emptyNotice(){return this._error||!this._lists?l:u`<div class="notice">
      ${this._t(this._lists.hidden.length?"allHidden":"empty")}
    </div>`}};k.properties={_config:{state:!0},_lists:{state:!0},_error:{state:!0},_editing:{state:!0}},k.styles=B`
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
  `;customElements.get("pareto-card")||(customElements.define("pareto-card",k),window.customCards=window.customCards??[],window.customCards.push({type:"pareto-card",name:"Pareto",description:"The entities you actually operate, ranked.",preview:!1,documentationURL:"https://github.com/dbackhove/ha-pareto"}));})();
