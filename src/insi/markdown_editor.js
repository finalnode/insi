import "toastui-editor-all";
import "de-de";

export default {
  template: `
    <div>
      <div ref="editorHost"></div>
      <div
        v-if="courseKind && validationVisible"
        class="insi-editor-validation-panel"
        role="status"
        aria-live="polite"
      >
        <div v-if="validationPending">M@rkdown wird geprüft …</div>
        <div v-else-if="validationIssues.length === 0" class="insi-validation-valid">
          ✓ M@rkdown ist gültig.
        </div>
        <template v-else>
          <strong>{{ validationIssues.length }} Problem{{ validationIssues.length === 1 ? '' : 'e' }}</strong>
          <button
            v-for="issue in validationIssues"
            :key="issue.line + '-' + issue.code"
            type="button"
            class="insi-validation-issue"
            @click="jumpToLine(issue.line)"
          >
            Zeile {{ issue.line }}: {{ issue.message }}
          </button>
        </template>
      </div>
    </div>
  `,
  props: {
    value: String,
    height: String,
    initialMode: String,
    courseKind: String,
    annotationItems: Array,
    disable: Boolean,
    resourcePath: String,
    id: String,
  },
  data() {
    return {
      editor: null,
      emitting: true,
      changeTimer: null,
      modeTimer: null,
      toolbarResizeTimer: null,
      modeSettling: false,
      currentMode: null,
      validationTimer: null,
      validationRequestId: 0,
      validationIssues: [],
      validationPending: false,
      validationVisible: false,
      validationButton: null,
      annotationMenu: null,
      documentClickHandler: null,
      modeSwitchHandler: null,
    };
  },
  mounted() {
    this.installStyles();
    const plugins = this.courseKind ? [this.createCoursePlugin()] : [];
    this.editor = new toastui.Editor({
      el: this.$refs.editorHost,
      height: this.height,
      initialEditType: this.initialMode,
      initialValue: this.value || "",
      language: "de-DE",
      previewStyle: "vertical",
      usageStatistics: false,
      plugins,
      toolbarItems: [
        ["heading", "bold", "italic", "strike"],
        ["hr", "quote"],
        ["ul", "ol", "task", "indent", "outdent"],
        ["table", "link"],
        ["code", "codeblock"],
        ["scrollSync"],
      ],
      events: {
        change: () => this.emitValue(),
        changeMode: mode => this.finishModeSwitch(mode),
      },
    });
    this.currentMode = this.editor.getCurrentMode();
    // Plugin buttons are inserted after TOAST has measured its toolbar once.
    // Trigger the built-in responsive calculation again so its overflow menu
    // also accounts for the in:si buttons.
    this.toolbarResizeTimer = setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
    }, 0);
    this.modeSwitchHandler = event => {
      if (event.target.closest(".toastui-editor-mode-switch .tab-item")) {
        this.beginModeSwitch();
      }
    };
    this.$refs.editorHost.addEventListener("mousedown", this.modeSwitchHandler, true);
    if (this.disable) this.setDisabled(true);
    if (this.courseKind) this.requestValidation();
  },
  beforeUnmount() {
    clearTimeout(this.changeTimer);
    clearTimeout(this.modeTimer);
    clearTimeout(this.toolbarResizeTimer);
    clearTimeout(this.validationTimer);
    if (this.documentClickHandler) {
      document.removeEventListener("click", this.documentClickHandler);
    }
    if (this.modeSwitchHandler) {
      this.$refs.editorHost.removeEventListener("mousedown", this.modeSwitchHandler, true);
    }
    if (this.annotationMenu) this.annotationMenu.remove();
    const element = mounted_app.elements[this.$props.id.slice(1)];
    if (element && this.editor) element.props.value = this.editor.getMarkdown();
    if (this.editor) this.editor.destroy();
  },
  watch: {
    value() { this.updateValue(); },
    disable(value) { this.setDisabled(value); },
    height(value) { if (this.editor) this.editor.setHeight(value); },
  },
  methods: {
    installStyles() {
      const stylesheetId = "insi-toastui-editor-css";
      if (!document.getElementById(stylesheetId)) {
        const stylesheet = document.createElement("link");
        stylesheet.id = stylesheetId;
        stylesheet.rel = "stylesheet";
        stylesheet.href = `${this.resourcePath}/toastui-editor.min.css`;
        document.head.appendChild(stylesheet);
      }
      const styleId = "insi-toastui-course-plugin-css";
      if (document.getElementById(styleId)) return;
      const style = document.createElement("style");
      style.id = styleId;
      style.textContent = `
        .insi-markdown-editor,
        .insi-markdown-editor .toastui-editor-defaultUI {
          box-sizing: border-box; min-width: 0; max-width: 100%;
        }
        .insi-markdown-editor .toastui-editor-defaultUI {
          overflow: hidden;
        }
        .insi-markdown-editor .toastui-editor-defaultUI-toolbar {
          box-sizing: border-box; width: 100%; min-width: 0; max-width: 100%;
          padding-inline: 6px; overflow-x: auto; overflow-y: hidden;
          scrollbar-width: thin; scrollbar-gutter: stable;
        }
        .insi-markdown-editor .toastui-editor-defaultUI-toolbar::-webkit-scrollbar { height: 6px; }
        .insi-markdown-editor .toastui-editor-defaultUI-toolbar button {
          margin-inline: 2px;
        }
        .insi-markdown-editor .toastui-editor-toolbar-item-wrapper {
          flex: 0 0 auto; margin-inline: 2px;
        }
        .insi-markdown-editor .toastui-editor-toolbar-divider {
          margin-inline: 5px;
        }
        .insi-markdown-editor .toastui-editor-toolbar-group {
          flex: 0 0 auto; min-width: max-content;
        }
        .insi-toolbar-button { background-image: none !important; font-weight: 700; width: 32px; }
        .insi-toolbar-button.insi-valid { color: #17823b; }
        .insi-toolbar-button.insi-invalid { color: #b42318; }
        .insi-annotation-wrapper { position: relative; flex: 0 0 auto; }
        .insi-annotation-menu { position: fixed; z-index: 5000;
          min-width: 190px; padding: 6px; border: 1px solid #dadde1; border-radius: 6px;
          background: white; box-shadow: 0 5px 18px rgba(0, 0, 0, .18); }
        .insi-annotation-menu[hidden] { display: none; }
        .insi-annotation-menu button { display: block; width: 100%; padding: 7px 10px;
          border: 0; border-radius: 4px; background: transparent; text-align: left; cursor: pointer; }
        .insi-annotation-menu button:hover { background: #eef3f8; }
        .insi-editor-validation-panel { margin-top: 8px; padding: 10px 12px;
          border: 1px solid #d7dce2; border-radius: 6px; background: #fafbfc; }
        .insi-validation-valid { color: #17823b; font-weight: 600; }
        .insi-validation-issue { display: block; width: 100%; margin-top: 5px; padding: 5px 7px;
          border: 0; border-radius: 4px; color: #b42318; background: transparent;
          text-align: left; cursor: pointer; }
        .insi-validation-issue:hover { background: #fff0ee; }
      `;
      document.head.appendChild(style);
    },
    createCoursePlugin() {
      const component = this;
      return function insiCoursePlugin() {
        return {
          toolbarItems: [
            {
              groupIndex: 5,
              itemIndex: 0,
              item: {
                name: "insiAnnotations",
                tooltip: "in:si-Annotation einfügen",
                el: component.createAnnotationMenu(),
              },
            },
            {
              groupIndex: 5,
              itemIndex: 1,
              item: {
                name: "insiValidation",
                tooltip: "M@rkdown prüfen",
                el: component.createValidationButton(),
              },
            },
          ],
        };
      };
    },
    toolbarButton(text, label) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "toastui-editor-toolbar-icons insi-toolbar-button";
      button.style.backgroundImage = "none";
      button.textContent = text;
      button.setAttribute("aria-label", label);
      return button;
    },
    createAnnotationMenu() {
      const wrapper = document.createElement("div");
      wrapper.className = "insi-annotation-wrapper";
      const trigger = this.toolbarButton("@", "in:si-Annotation einfügen");
      const menu = document.createElement("div");
      menu.className = "insi-annotation-menu";
      menu.hidden = true;
      for (const annotation of this.annotationItems || []) {
        const item = document.createElement("button");
        item.type = "button";
        item.textContent = annotation.label;
        item.addEventListener("click", event => {
          event.stopPropagation();
          menu.hidden = true;
          this.insertText(annotation.text, true);
        });
        menu.appendChild(item);
      }
      trigger.addEventListener("click", event => {
        event.stopPropagation();
        const opening = menu.hidden;
        menu.hidden = !opening;
        if (opening) {
          const bounds = trigger.getBoundingClientRect();
          menu.style.top = `${bounds.bottom + 4}px`;
          menu.style.right = `${Math.max(8, window.innerWidth - bounds.right)}px`;
        }
      });
      wrapper.append(trigger);
      document.body.appendChild(menu);
      this.annotationMenu = menu;
      this.documentClickHandler = () => { menu.hidden = true; };
      document.addEventListener("click", this.documentClickHandler);
      return wrapper;
    },
    createValidationButton() {
      const button = this.toolbarButton("…", "M@rkdown wird geprüft");
      button.addEventListener("click", () => {
        this.validationVisible = !this.validationVisible;
      });
      this.validationButton = button;
      return button;
    },
    updateValidationButton() {
      if (!this.validationButton) return;
      this.validationButton.classList.remove("insi-valid", "insi-invalid");
      if (this.validationPending) {
        this.validationButton.textContent = "…";
        this.validationButton.title = "M@rkdown wird geprüft";
      } else if (this.validationIssues.length === 0) {
        this.validationButton.textContent = "✓";
        this.validationButton.title = "M@rkdown ist gültig";
        this.validationButton.classList.add("insi-valid");
      } else {
        this.validationButton.textContent = `!${this.validationIssues.length}`;
        this.validationButton.title = `${this.validationIssues.length} M@rkdown-Problem(e)`;
        this.validationButton.classList.add("insi-invalid");
      }
    },
    emitValue() {
      if (!this.emitting || !this.editor || this.modeSettling) return;
      clearTimeout(this.changeTimer);
      this.changeTimer = setTimeout(() => {
        this.emitCurrentValue();
      }, 180);
    },
    beginModeSwitch() {
      if (!this.editor || this.modeSettling) return;
      clearTimeout(this.changeTimer);
      clearTimeout(this.validationTimer);
      clearTimeout(this.modeTimer);
      this.modeSettling = true;
      // TOAST emits several document changes while converting its internal
      // Markdown model to ProseMirror (and back). None of these intermediate
      // states may be sent through NiceGUI: feeding one of them back into
      // setMarkdown can recursively restart the conversion and block the UI.
      this.emitting = false;
      this.validationPending = false;
      this.updateValidationButton();
      // Clicking the already active tab produces no changeMode event. Restore
      // normal editing in that case as well.
      this.modeTimer = setTimeout(() => {
        if (this.editor && this.modeSettling) {
          this.finishModeSwitch(this.editor.getCurrentMode());
        }
      }, 1000);
    },
    finishModeSwitch(mode) {
      if (!this.editor) return;
      if (!this.modeSettling && mode === this.currentMode) return;
      clearTimeout(this.changeTimer);
      clearTimeout(this.validationTimer);
      clearTimeout(this.modeTimer);
      this.currentMode = mode;
      this.$nextTick(() => {
        if (!this.editor) return;
        this.modeSettling = false;
        this.emitting = true;
        this.emitCurrentValue(false);
        this.requestValidation();
      });
    },
    emitCurrentValue(validate = true) {
      if (!this.editor) return;
      this.$emit("update:value", this.editor.getMarkdown());
      if (validate) this.requestValidation();
    },
    requestValidation() {
      if (!this.courseKind || !this.editor || this.modeSettling) return;
      clearTimeout(this.validationTimer);
      if (!this.validationPending) {
        this.validationPending = true;
        this.updateValidationButton();
      }
      this.validationTimer = setTimeout(() => {
        this.validationRequestId += 1;
        this.$emit("validation", {
          markdown: this.editor.getMarkdown(),
          request_id: this.validationRequestId,
        });
      }, 500);
    },
    setValidation(payload) {
      if (!payload || payload.request_id !== this.validationRequestId) return;
      if (this.modeSettling) {
        this.validationPending = false;
        this.updateValidationButton();
        return;
      }
      this.validationIssues = Array.isArray(payload.issues) ? payload.issues : [];
      this.validationPending = false;
      this.updateValidationButton();
    },
    updateValue() {
      if (!this.editor) return;
      const next = this.value || "";
      if (this.editor.getMarkdown() === next) return;
      this.emitting = false;
      this.editor.setMarkdown(next, false);
      this.$nextTick(() => {
        this.emitting = true;
        this.requestValidation();
      });
    },
    insertText(text, markdownMode) {
      if (!this.editor) return;
      if (markdownMode) this.editor.changeMode("markdown", true);
      this.editor.insertText(text);
      this.editor.focus();
      this.$emit("update:value", this.editor.getMarkdown());
      this.requestValidation();
    },
    jumpToLine(line) {
      if (!this.editor || !Number.isInteger(line) || line < 1) return;
      this.editor.changeMode("markdown", true);
      this.$nextTick(() => {
        this.editor.setSelection([line, 1], [line, 1]);
        this.editor.focus();
      });
    },
    setMode(mode) {
      if (this.editor) this.editor.changeMode(mode, true);
    },
    setDisabled(disabled) {
      if (!this.editor) return;
      const root = this.$refs.editorHost;
      root.style.pointerEvents = disabled ? "none" : "";
      root.style.opacity = disabled ? "0.65" : "";
    },
  },
};
