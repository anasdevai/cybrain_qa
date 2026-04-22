/**
 * PlaceholderSuggestion.js
 * 
 * Provides an autocomplete suggestion mechanism for Tiptap.
 * When a user types the trigger character (by default '{' or '{{'), 
 * a popup appears offering a list of available placeholder variables.
 * Selecting a variable inserts it into the editor as `{{variableName}}`.
 */

import { Extension } from '@tiptap/core';
import Suggestion from '@tiptap/suggestion';

/**
 * Creates the DOM elements and interaction logic for the suggestion dropdown list.
 * 
 * @param {Array} items - The initial list of suggestion items (strings).
 * @returns {Object} An object containing the container element, an update method, and a keydown handler.
 */
function createSuggestionList(items = []) {
    // Main container for the dropdown menu
    const container = document.createElement('div');
    container.className = 'placeholder-suggestion-list';

    // Wrapper for the individual suggestion items
    const list = document.createElement('div');
    list.className = 'placeholder-suggestion-items';
    container.appendChild(list);

    let selectedIndex = 0; // Tracks the currently highlighted item via keyboard navigation
    let currentItems = items; // Holds the currently filtered items available for selection
    let command = null; // The function to execute when an item is selected

    /**
     * Re-renders the list of suggestion buttons based on the current items.
     */
    const renderItems = () => {
        // Clear existing items
        list.innerHTML = '';

        // Render an empty state if no variables match the query
        if (!currentItems.length) {
            const empty = document.createElement('div');
            empty.className = 'placeholder-suggestion-empty';
            empty.textContent = 'No placeholders found';
            list.appendChild(empty);
            return;
        }

        // Render each matching item as a button
        currentItems.forEach((item, index) => {
            const button = document.createElement('button');
            button.type = 'button';
            // Apply a selected class if the item matches the current keyboard selection index
            button.className = `placeholder-suggestion-item ${index === selectedIndex ? 'is-selected' : ''
                }`;
            button.textContent = item;

            // Handle mouse clicks on items
            button.addEventListener('mousedown', (event) => {
                event.preventDefault(); // Prevent editor from losing focus
                if (command) {
                    command(item); // Execute selection command
                }
            });

            list.appendChild(button);
        });
    };

    // Initial render
    renderItems();

    return {
        // Expose the raw DOM element for rendering in a popup
        element: container,

        /**
         * Update the available items or active command, then re-render.
         * Called when the user continues typing.
         */
        update(props) {
            currentItems = props.items || [];
            command = props.command;

            // Reset selection to the start if the previous index is out of bounds
            if (selectedIndex >= currentItems.length) {
                selectedIndex = 0;
            }

            renderItems();
        },

        /**
         * Handles keyboard navigation and selection within the suggestion menu.
         * @returns {boolean} True if the event was handled, false otherwise.
         */
        onKeyDown(props) {
            if (!currentItems.length) return false;

            // Navigate up the list (wrapping around to bottom)
            if (props.event.key === 'ArrowUp') {
                selectedIndex =
                    (selectedIndex + currentItems.length - 1) % currentItems.length;
                renderItems();
                return true;
            }

            // Navigate down the list (wrapping around to top)
            if (props.event.key === 'ArrowDown') {
                selectedIndex = (selectedIndex + 1) % currentItems.length;
                renderItems();
                return true;
            }

            // Select the highlighted item
            if (props.event.key === 'Enter') {
                props.event.preventDefault();
                if (command && currentItems[selectedIndex]) {
                    command(currentItems[selectedIndex]);
                    return true;
                }
            }

            return false; // Event not handled
        },
    };
}

/**
 * PlaceholderSuggestion Extension
 * 
 * Registers the suggestion functionality with Tiptap.
 * Listens for the configured trigger character and displays the suggestion list relative to the cursor.
 */
export const PlaceholderSuggestion = Extension.create({
    name: 'placeholderSuggestion',

    // Define configuration options for the extension
    addOptions() {
        return {
            suggestion: {
                char: '{', // Character that triggers the suggestions
                allowSpaces: false, // Prevent matching if there are spaces after the trigger
                startOfLine: false, // Allow triggering anywhere in the line, not just the start

                allowedPrefixes: null,

                /**
                 * Filters the available items based on user input.
                 */
                items: ({ editor, query }) => {
                    // Pull variable definitions from editor storage (must be populated externally)
                    const variableNames =
                        editor.storage.placeholderSuggestion?.items || [];

                    // Strip any leading brackets to cleanly match against stored names
                    const normalizedQuery = (query || '').replace(/^\{/, '').trim();

                    // Case-insensitive filtering
                    return variableNames.filter((item) =>
                        item.toLowerCase().includes(normalizedQuery.toLowerCase())
                    );
                },

                /**
                 * Replaces the currently matched text stream with the selected variable.
                 */
                command: ({ editor, range, props }) => {
                    const from = range.from;
                    const to = range.to;

                    // Inspect text directly before the matched range to handle '{{' cleanly
                    const textBefore = editor.state.doc.textBetween(
                        Math.max(0, from - 2),
                        from,
                        '\0',
                        '\0'
                    );

                    // If user typed '{{', replace both brackets
                    if (textBefore === '{{') {
                        editor
                            .chain()
                            .focus()
                            .deleteRange({ from: from - 2, to })
                            .insertContent(`{{${props}}}`) // Format as {{variable}}
                            .run();
                        return;
                    }

                    // Standard replacement
                    editor
                        .chain()
                        .focus()
                        .deleteRange(range)
                        .insertContent(`{{${props}}}`)
                        .run();
                },

                /**
                 * Ensure the trigger is specifically '{{' or similar (custom logic).
                 */
                allow: ({ state, range }) => {
                    const textBefore = state.doc.textBetween(
                        Math.max(0, range.from - 2),
                        range.from,
                        '\0',
                        '\0'
                    );

                    return textBefore === '{{';
                },

                /**
                 * Coordinates the rendering of the popup element via vanilla DOM.
                 */
                render: () => {
                    let popup; // Container added to body
                    let component; // The suggestion UI list defined above

                    return {
                        onStart: (props) => {
                            component = createSuggestionList(props.items);
                            component.update(props);

                            // Create a fixed floating container
                            popup = document.createElement('div');
                            popup.className = 'placeholder-suggestion-popup';
                            popup.appendChild(component.element);
                            document.body.appendChild(popup);

                            // Position popup underneath current cursor
                            const rect = props.clientRect?.();
                            if (rect) {
                                popup.style.left = `${rect.left + window.scrollX}px`;
                                popup.style.top = `${rect.bottom + window.scrollY + 6}px`;
                            }
                        },

                        onUpdate(props) {
                            component?.update(props);

                            // Update popup position as user types (and cursor shifts)
                            const rect = props.clientRect?.();
                            if (rect && popup) {
                                popup.style.left = `${rect.left + window.scrollX}px`;
                                popup.style.top = `${rect.bottom + window.scrollY + 6}px`;
                            }
                        },

                        onKeyDown(props) {
                            // Dismiss popup via Escape root capability
                            if (props.event.key === 'Escape') {
                                if (popup) popup.remove();
                                return true;
                            }

                            // Defer other events (arrow up/down) to internal handler
                            return component?.onKeyDown(props) || false;
                        },

                        onExit() {
                            // Clean up DOM on exit
                            if (popup) {
                                popup.remove();
                                popup = null;
                            }
                        },
                    };
                },
            },
        };
    },

    // Provides custom state logic on the editor for extensions to use
    addStorage() {
        return {
            items: [], // Holds the list of dynamically updated variables
        };
    },

    // Links config into ProseMirror registry
    addProseMirrorPlugins() {
        return [
            Suggestion({
                editor: this.editor,
                ...this.options.suggestion,
            }),
        ];
    },
});