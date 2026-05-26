// ---- packages/react/src/toolbar/button/ToolbarButton.test.tsx ----
import { expect, vi } from 'vitest';
import { Toolbar } from '@base-ui/react/toolbar';
import { Switch } from '@base-ui/react/switch';
import { Menu } from '@base-ui/react/menu';
import { Select } from '@base-ui/react/select';
import { Dialog } from '@base-ui/react/dialog';
import { AlertDialog } from '@base-ui/react/alert-dialog';
import { Popover } from '@base-ui/react/popover';
import { Toggle } from '@base-ui/react/toggle';
import { ToggleGroup } from '@base-ui/react/toggle-group';
import { screen, waitFor } from '@mui/internal-test-utils';
import { createRenderer, describeConformance, isJSDOM } from '#test-utils';
import { NOOP } from '../../internals/noop';
import { ToolbarRootContext } from '../root/ToolbarRootContext';
import { CompositeRootContext } from '../../internals/composite/root/CompositeRootContext';

const testCompositeContext: CompositeRootContext = {
  highlightedIndex: 0,
  onHighlightedIndexChange: NOOP,
  highlightItemOnHover: false,
  relayKeyboardEvent: NOOP,
};

const testToolbarContext: ToolbarRootContext = {
  disabled: false,
  orientation: 'horizontal',
  setItemMap: NOOP,
};

describe('<Toolbar.Button />', () => {
  const { render } = createRenderer();

  describeConformance(<Toolbar.Button />, () => ({
    refInstanceof: window.HTMLButtonElement,
    testComponentPropWith: 'button',
    button: true,
    render: (node) => {
      return render(
        <ToolbarRootContext.Provider value={testToolbarContext}>
          <CompositeRootContext.Provider value={testCompositeContext}>
            {node}
          </CompositeRootContext.Provider>
        </ToolbarRootContext.Provider>,
      );
    },
  }));

  describe('ARIA attributes', () => {
    it('renders a button', async () => {
      await render(
        <Toolbar.Root>
          <Toolbar.Button data-testid="button" />
        </Toolbar.Root>,
      );

      expect(screen.getByTestId('button')).toBe(screen.getByRole('button'));
    });
  });

  describe('prop: disabled', () => {
    it('disables the button', async () => {
      const handleClick = vi.fn();
      const handleMouseDown = vi.fn().mockName('handleMouseDown');
      const handlePointerDown = vi.fn();
      const handleKeyDown = vi.fn();

      const { user } = await render(
        <Toolbar.Root>
          <Toolbar.Button
            disabled
            onClick={handleClick}
            onMouseDown={handleMouseDown}
            onPointerDown={handlePointerDown}
            onKeyDown={handleKeyDown}
          />
        </Toolbar.Root>,
      );

      const button = screen.getByRole('button');

      expect(button).not.toHaveAttribute('disabled');
      expect(button).toHaveAttribute('data-disabled');
      expect(button).toHaveAttribute('aria-disabled', 'true');

      await user.click(button);
      await user.keyboard(`[Space]`);
      await user.keyboard(`[Enter]`);
      expect(handleClick).toHaveBeenCalledTimes(0);
      expect(handleMouseDown).toHaveBeenCalledTimes(0);
      expect(handlePointerDown).toHaveBeenCalledTimes(0);
      expect(handleKeyDown).toHaveBeenCalledTimes(0);
    });
  });

  describe('rendering other Base UI components', () => {
    describe('Switch', () => {
      it('renders a switch', async () => {
        vi.spyOn(console, 'error')
          .mockName('console.error')
          .mockImplementation(() => {});

        await render(
          <Toolbar.Root>
            <Toolbar.Button data-testid="button" render={<Switch.Root />} />
          </Toolbar.Root>,
        );

        expect(console.error).toHaveBeenCalledTimes(1);
        expect(console.error).toHaveBeenCalledWith(
          expect.stringContaining(
            'Base UI: A component that acts as a button expected a native <button> because ' +
              'the `nativeButton` prop is true. Rendering a non-<button> removes native button semantics, ' +
              'which can impact forms and accessibility. Use a real <button> in the `render` prop, or ' +
              'set `nativeButton` to `false`.',
          ),
        );

        expect(screen.getByTestId('button')).toBe(screen.getByRole('switch'));
      });

      it('handles interactions', async () => {
        vi.spyOn(console, 'error')
          .mockName('console.error')
          .mockImplementation(() => {});

        const handleCheckedChange = vi.fn();
        const handleClick = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Toolbar.Button
              onClick={handleClick}
              render={<Switch.Root defaultChecked={false} onCheckedChange={handleCheckedChange} />}
            />
          </Toolbar.Root>,
        );

        expect(console.error).toHaveBeenCalledTimes(1);
        expect(console.error).toHaveBeenCalledWith(
          expect.stringContaining(
            'Base UI: A component that acts as a button expected a native <button> because ' +
              'the `nativeButton` prop is true. Rendering a non-<button> removes native button semantics, ' +
              'which can impact forms and accessibility. Use a real <button> in the `render` prop, or ' +
              'set `nativeButton` to `false`.',
          ),
        );

        const switchElement = screen.getByRole('switch');
        expect(switchElement).toHaveAttribute('data-unchecked');

        await user.keyboard('[Tab]');
        expect(switchElement).toHaveAttribute('tabindex', '0');

        await user.click(switchElement);
        expect(handleCheckedChange).toHaveBeenCalledTimes(1);
        expect(handleClick).toHaveBeenCalledTimes(1);
        expect(switchElement).toHaveAttribute('data-checked');

        await user.keyboard('[Enter]');
        expect(handleCheckedChange).toHaveBeenCalledTimes(2);
        expect(handleClick).toHaveBeenCalledTimes(2);
        expect(switchElement).toHaveAttribute('data-unchecked');

        await user.keyboard('[Space]');
        expect(handleCheckedChange).toHaveBeenCalledTimes(3);
        expect(handleClick).toHaveBeenCalledTimes(3);
        expect(switchElement).toHaveAttribute('data-checked');
      });

      it('disabled state', async () => {
        vi.spyOn(console, 'error')
          .mockName('console.error')
          .mockImplementation(() => {});

        const handleCheckedChange = vi.fn();
        const handleClick = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Toolbar.Button
              disabled
              onClick={handleClick}
              render={<Switch.Root onCheckedChange={handleCheckedChange} />}
            />
          </Toolbar.Root>,
        );

        expect(console.error).toHaveBeenCalledTimes(1);
        expect(console.error).toHaveBeenCalledWith(
          expect.stringContaining(
            'Base UI: A component that acts as a button expected a native <button> because ' +
              'the `nativeButton` prop is true. Rendering a non-<button> removes native button semantics, ' +
              'which can impact forms and accessibility. Use a real <button> in the `render` prop, or ' +
              'set `nativeButton` to `false`.',
          ),
        );

        const switchElement = screen.getByRole('switch');

        expect(switchElement).not.toHaveAttribute('disabled');
        expect(switchElement).toHaveAttribute('data-disabled');
        expect(switchElement).toHaveAttribute('aria-disabled', 'true');

        await user.keyboard('[Tab]');
        expect(switchElement).toHaveAttribute('tabindex', '0');

        await user.keyboard('[Enter]');
        expect(handleCheckedChange).toHaveBeenCalledTimes(0);
        expect(handleClick).toHaveBeenCalledTimes(0);

        await user.keyboard('[Space]');
        expect(handleCheckedChange).toHaveBeenCalledTimes(0);
        expect(handleClick).toHaveBeenCalledTimes(0);

        await user.click(switchElement);
        expect(handleCheckedChange).toHaveBeenCalledTimes(0);
        expect(handleClick).toHaveBeenCalledTimes(0);
      });
    });

    describe('Menu', () => {
      it('renders a menu trigger', async () => {
        await render(
          <Toolbar.Root>
            <Menu.Root>
              <Toolbar.Button data-testid="button" render={<Menu.Trigger>Toggle</Menu.Trigger>} />
              <Menu.Portal>
                <Menu.Positioner>
                  <Menu.Popup>
                    <Menu.Item data-testid="item-1">1</Menu.Item>
                    <Menu.Item data-testid="item-2">2</Menu.Item>
                    <Menu.Item data-testid="item-3">3</Menu.Item>
                  </Menu.Popup>
                </Menu.Positioner>
              </Menu.Portal>
            </Menu.Root>
          </Toolbar.Root>,
        );

        expect(screen.getByTestId('button')).toHaveAttribute('aria-haspopup', 'menu');
      });

      it('handles interactions', async () => {
        const handleOpenChange = vi.fn();
        const handleClick = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Menu.Root onOpenChange={handleOpenChange}>
              <Toolbar.Button
                data-testid="button"
                onClick={handleClick}
                render={<Menu.Trigger>Toggle</Menu.Trigger>}
              />
              <Menu.Portal>
                <Menu.Positioner>
                  <Menu.Popup>
                    <Menu.Item data-testid="item-1">1</Menu.Item>
                    <Menu.Item data-testid="item-2">2</Menu.Item>
                    <Menu.Item data-testid="item-3">3</Menu.Item>
                  </Menu.Popup>
                </Menu.Positioner>
              </Menu.Portal>
            </Menu.Root>
          </Toolbar.Root>,
        );

        expect(screen.queryByRole('menu')).toBe(null);

        const trigger = screen.getByRole('button', { name: 'Toggle' });

        await user.keyboard('[Tab]');
        expect(trigger).toHaveFocus();

        await user.keyboard('[Enter]');
        expect(handleClick).toHaveBeenCalledTimes(1);
        expect(handleOpenChange).toHaveBeenCalledTimes(1);
        expect(screen.queryByRole('menu')).not.toBe(null);

        await waitFor(() => {
          expect(screen.getByTestId('item-1')).toHaveFocus();
        });

        await user.keyboard('[ArrowDown]');
        await waitFor(() => {
          expect(screen.getByTestId('item-2')).toHaveFocus();
        });

        await user.keyboard('[ArrowDown]');
        await waitFor(() => {
          expect(screen.getByTestId('item-3')).toHaveFocus();
        });

        await user.keyboard('[ArrowUp]');
        await waitFor(() => {
          expect(screen.getByTestId('item-2')).toHaveFocus();
        });

        await user.keyboard('[Escape]');
        await waitFor(() => {
          expect(screen.queryByRole('menu')).toBe(null);
        });

        expect(handleOpenChange).toHaveBeenCalledTimes(2);

        await waitFor(() => {
          expect(trigger).toHaveFocus();
        });
      });

      it('disabled state', async () => {
        const handleOpenChange = vi.fn();
        const handleClick = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Menu.Root onOpenChange={handleOpenChange}>
              <Toolbar.Button
                data-testid="button"
                disabled
                onClick={handleClick}
                render={<Menu.Trigger>Toggle</Menu.Trigger>}
              />
              <Menu.Portal>
                <Menu.Positioner>
                  <Menu.Popup>
                    <Menu.Item data-testid="item-1">1</Menu.Item>
                    <Menu.Item data-testid="item-2">2</Menu.Item>
                    <Menu.Item data-testid="item-3">3</Menu.Item>
                  </Menu.Popup>
                </Menu.Positioner>
              </Menu.Portal>
            </Menu.Root>
          </Toolbar.Root>,
        );

        const trigger = screen.getByRole('button', { name: 'Toggle' });
        expect(trigger).not.toHaveAttribute('disabled');
        expect(trigger).toHaveAttribute('data-disabled');
        expect(trigger).toHaveAttribute('aria-disabled', 'true');

        expect(screen.queryByRole('menu')).toBe(null);

        await user.keyboard('[Tab]');
        expect(trigger).toHaveFocus();

        await user.keyboard('[Enter]');
        await user.keyboard('[Space]');
        await user.keyboard('[ArrowUp]');
        await user.keyboard('[ArrowDown]');

        expect(handleClick).toHaveBeenCalledTimes(0);
        expect(handleOpenChange).toHaveBeenCalledTimes(0);
        expect(screen.queryByRole('menu')).toBe(null);
      });
    });

    describe('Select', () => {
      it('renders a select trigger', async () => {
        await render(
          <Toolbar.Root>
            <Select.Root defaultValue="a">
              <Toolbar.Button data-testid="button" render={<Select.Trigger />} />
              <Select.Portal>
                <Select.Positioner>
                  <Select.Popup>
                    <Select.Item value="a">a</Select.Item>
                    <Select.Item value="b">b</Select.Item>
                  </Select.Popup>
                </Select.Positioner>
              </Select.Portal>
            </Select.Root>
          </Toolbar.Root>,
        );

        const trigger = screen.getByTestId('button');
        expect(trigger).toBe(screen.getByRole('combobox'));
        expect(trigger).toHaveAttribute('aria-haspopup', 'listbox');
      });

      it.skipIf(!isJSDOM)('handles interactions', async () => {
        const handleValueChange = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Select.Root defaultValue="a" onValueChange={handleValueChange}>
              <Toolbar.Button data-testid="button" render={<Select.Trigger />} />
              <Select.Portal>
                <Select.Positioner>
                  <Select.Popup data-testid="popup">
                    <Select.Item value="a" data-testid="item-a">
                      a
                    </Select.Item>
                    <Select.Item value="b" data-testid="item-b">
                      b
                    </Select.Item>
                  </Select.Popup>
                </Select.Positioner>
              </Select.Portal>
            </Select.Root>
          </Toolbar.Root>,
        );

        expect(screen.queryByRole('listbox')).toBe(null);

        const trigger = screen.getByTestId('button');
        await user.keyboard('[Tab]');
        expect(trigger).toHaveFocus();

        await user.keyboard('[ArrowDown]');
        expect(screen.queryByRole('listbox')).toBe(screen.getByTestId('popup'));
        await waitFor(() => {
          expect(screen.getByRole('option', { name: 'a' })).toHaveFocus();
        });

        await user.keyboard('[ArrowDown]');
        await waitFor(() => {
          expect(screen.getByRole('option', { name: 'b' })).toHaveFocus();
        });

        await user.keyboard('[Enter]');
        await waitFor(() => {
          expect(screen.queryByRole('listbox')).toBe(null);
        });

        await waitFor(() => {
          expect(trigger).toHaveFocus();
        });

        expect(handleValueChange).toHaveBeenCalledTimes(1);
        expect(handleValueChange).toHaveBeenCalledWith('b', expect.anything());
      });

      it('disabled state', async () => {
        await expect(async () => {
          const onValueChange = vi.fn();
          const onOpenChange = vi.fn();
          const { user } = await render(
            <Toolbar.Root>
              <Select.Root
                defaultValue="a"
                onValueChange={onValueChange}
                onOpenChange={onOpenChange}
              >
                <Toolbar.Button disabled render={<Select.Trigger nativeButton={false} />} />
                <Select.Portal>
                  <Select.Positioner>
                    <Select.Popup>
                      <Select.Item value="a" />
                      <Select.Item value="b" />
                    </Select.Popup>
                  </Select.Positioner>
                </Select.Portal>
              </Select.Root>
            </Toolbar.Root>,
          );

          expect(screen.queryByRole('listbox')).toBe(null);

          const trigger = screen.getByRole('combobox');
          expect(trigger).not.toHaveAttribute('disabled');
          expect(trigger).toHaveAttribute('data-disabled');
          expect(trigger).toHaveAttribute('aria-disabled', 'true');

          await user.keyboard('[Tab]');
          expect(trigger).toHaveFocus();

          expect(onOpenChange).toHaveBeenCalledTimes(0);
          expect(onValueChange).toHaveBeenCalledTimes(0);

          await user.keyboard('[ArrowUp]');
          await user.keyboard('[ArrowDown]');
          await user.keyboard('[Enter]');
          await user.keyboard('[Space]');

          expect(onOpenChange).toHaveBeenCalledTimes(0);
          expect(onValueChange).toHaveBeenCalledTimes(0);
        }).toErrorDev([
          'Base UI: A component that acts as a button expected a non-<button> because ' +
            'the `nativeButton` prop is false. Rendering a <button> keeps native behavior while Base UI ' +
            'applies non-native attributes and handlers, which can add unintended extra attributes ' +
            '(such as `role` or `aria-disabled`). Use a non-<button> in the `render` prop, or set ' +
            '`nativeButton` to `true`.',
        ]);
      });
    });

    describe('Dialog', () => {
      it('renders a dialog trigger', async () => {
        await render(
          <Toolbar.Root>
            <Dialog.Root modal={false}>
              <Toolbar.Button render={<Dialog.Trigger data-testid="trigger" />} />
              <Dialog.Portal>
                <Dialog.Backdrop />
                <Dialog.Popup>
                  <Dialog.Title>title text</Dialog.Title>
                </Dialog.Popup>
              </Dialog.Portal>
            </Dialog.Root>
          </Toolbar.Root>,
        );

        expect(screen.getByTestId('trigger')).toBe(screen.getByRole('button'));
      });

      it('handles interactions', async () => {
        const onOpenChange = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Dialog.Root modal={false} onOpenChange={onOpenChange}>
              <Toolbar.Button render={<Dialog.Trigger />} />
              <Dialog.Portal>
                <Dialog.Backdrop />
                <Dialog.Popup>
                  <Dialog.Title>title text</Dialog.Title>
                </Dialog.Popup>
              </Dialog.Portal>
            </Dialog.Root>
          </Toolbar.Root>,
        );

        expect(screen.queryByText('title text')).toBe(null);

        const trigger = screen.getByRole('button');
        await user.keyboard('[Tab]');
        expect(trigger).toHaveFocus();
        expect(onOpenChange).toHaveBeenCalledTimes(0);

        await user.keyboard('[Enter]');
        expect(screen.queryByText('title text')).not.toBe(null);
        expect(onOpenChange).toHaveBeenCalledTimes(1);
        expect(onOpenChange).toHaveBeenNthCalledWith(1, true, expect.anything());

        await user.keyboard('[Escape]');
        expect(screen.queryByText('title text')).toBe(null);
        expect(onOpenChange).toHaveBeenCalledTimes(2);
        expect(onOpenChange).toHaveBeenNthCalledWith(2, false, expect.anything());

        await waitFor(() => {
          expect(trigger).toHaveFocus();
        });
      });

      it('disabled state', async () => {
        const onOpenChange = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Dialog.Root modal={false} onOpenChange={onOpenChange}>
              <Toolbar.Button disabled render={<Dialog.Trigger />} />
              <Dialog.Portal>
                <Dialog.Backdrop />
                <Dialog.Popup>
                  <Dialog.Title>title text</Dialog.Title>
                </Dialog.Popup>
              </Dialog.Portal>
            </Dialog.Root>
          </Toolbar.Root>,
        );

        expect(screen.queryByText('title text')).toBe(null);

        const trigger = screen.getByRole('button');
        expect(trigger).not.toHaveAttribute('disabled');
        expect(trigger).toHaveAttribute('data-disabled');
        expect(trigger).toHaveAttribute('aria-disabled', 'true');

        await user.keyboard('[Tab]');
        expect(trigger).toHaveFocus();
        expect(onOpenChange).toHaveBeenCalledTimes(0);

        await user.keyboard('[Enter]');
        await user.keyboard('[Space]');
        await user.keyboard('[ArrowUp]');
        await user.keyboard('[ArrowDown]');
        expect(onOpenChange).toHaveBeenCalledTimes(0);
      });

      it('prevents composite keydowns from escaping', async () => {
        const onOpenChange = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Dialog.Root modal={false} onOpenChange={onOpenChange}>
              <Toolbar.Button render={<Dialog.Trigger />}>dialog</Toolbar.Button>
              <Dialog.Portal>
                <Dialog.Popup />
              </Dialog.Portal>
            </Dialog.Root>

            <Toolbar.Button>empty</Toolbar.Button>
          </Toolbar.Root>,
        );

        expect(screen.queryByRole('dialog')).toBe(null);

        const trigger = screen.getByRole('button', { name: 'dialog' });
        await user.click(trigger);

        await waitFor(() => {
          expect(screen.queryByRole('dialog')).toHaveFocus();
        });

        await user.keyboard('{ArrowRight}');

        expect(onOpenChange).toHaveBeenLastCalledWith(true, expect.anything());
      });
    });

    describe('AlertDialog', () => {
      it('renders an alert dialog trigger', async () => {
        await render(
          <Toolbar.Root>
            <AlertDialog.Root>
              <Toolbar.Button render={<AlertDialog.Trigger data-testid="trigger" />} />
              <AlertDialog.Portal>
                <AlertDialog.Backdrop />
                <AlertDialog.Popup>
                  <AlertDialog.Title>title text</AlertDialog.Title>
                </AlertDialog.Popup>
              </AlertDialog.Portal>
            </AlertDialog.Root>
          </Toolbar.Root>,
        );

        expect(screen.getByTestId('trigger')).toBe(screen.getByRole('button'));
      });

      it('handles interactions', async () => {
        const onOpenChange = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <AlertDialog.Root onOpenChange={onOpenChange}>
              <Toolbar.Button render={<AlertDialog.Trigger />} />
              <AlertDialog.Portal>
                <AlertDialog.Backdrop />
                <AlertDialog.Popup>
                  <AlertDialog.Title>title text</AlertDialog.Title>
                </AlertDialog.Popup>
              </AlertDialog.Portal>
            </AlertDialog.Root>
          </Toolbar.Root>,
        );

        expect(screen.queryByText('title text')).toBe(null);

        const trigger = screen.getByRole('button');
        await user.keyboard('[Tab]');
        expect(trigger).toHaveFocus();
        expect(onOpenChange).toHaveBeenCalledTimes(0);

        await user.keyboard('[Enter]');
        expect(screen.queryByText('title text')).not.toBe(null);
        expect(onOpenChange).toHaveBeenCalledTimes(1);
        expect(onOpenChange).toHaveBeenNthCalledWith(1, true, expect.anything());

        await user.keyboard('[Escape]');
        expect(screen.queryByText('title text')).toBe(null);
        expect(onOpenChange).toHaveBeenCalledTimes(2);
        expect(onOpenChange).toHaveBeenNthCalledWith(2, false, expect.anything());

        await waitFor(() => {
          expect(trigger).toHaveFocus();
        });
      });

      it('disabled state', async () => {
        const onOpenChange = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <AlertDialog.Root onOpenChange={onOpenChange}>
              <Toolbar.Button disabled render={<AlertDialog.Trigger />} />
              <AlertDialog.Portal>
                <AlertDialog.Backdrop />
                <AlertDialog.Popup>
                  <AlertDialog.Title>title text</AlertDialog.Title>
                </AlertDialog.Popup>
              </AlertDialog.Portal>
            </AlertDialog.Root>
          </Toolbar.Root>,
        );

        expect(screen.queryByText('title text')).toBe(null);

        const trigger = screen.getByRole('button');
        expect(trigger).not.toHaveAttribute('disabled');
        expect(trigger).toHaveAttribute('data-disabled');
        expect(trigger).toHaveAttribute('aria-disabled', 'true');

        await user.keyboard('[Tab]');
        expect(trigger).toHaveFocus();
        expect(onOpenChange).toHaveBeenCalledTimes(0);

        await user.keyboard('[Enter]');
        await user.keyboard('[Space]');
        await user.keyboard('[ArrowUp]');
        await user.keyboard('[ArrowDown]');
        expect(onOpenChange).toHaveBeenCalledTimes(0);
      });

      it('prevents composite keydowns from escaping', async () => {
        const onOpenChange = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <AlertDialog.Root onOpenChange={onOpenChange}>
              <Toolbar.Button render={<AlertDialog.Trigger />}>dialog</Toolbar.Button>
              <AlertDialog.Portal>
                <AlertDialog.Popup />
              </AlertDialog.Portal>
            </AlertDialog.Root>

            <Toolbar.Button>empty</Toolbar.Button>
          </Toolbar.Root>,
        );

        expect(screen.queryByRole('dialog')).toBe(null);

        const trigger = screen.getByRole('button', { name: 'dialog' });
        await user.click(trigger);

        await waitFor(() => {
          expect(screen.queryByRole('alertdialog')).toHaveFocus();
        });

        await user.keyboard('{ArrowRight}');

        expect(onOpenChange).toHaveBeenLastCalledWith(true, expect.anything());
      });
    });

    describe('Popover', () => {
      it('renders a popover trigger', async () => {
        await render(
          <Toolbar.Root>
            <Popover.Root>
              <Toolbar.Button render={<Popover.Trigger data-testid="trigger" />} />
              <Popover.Portal>
                <Popover.Positioner>
                  <Popover.Popup>Content</Popover.Popup>
                </Popover.Positioner>
              </Popover.Portal>
            </Popover.Root>
          </Toolbar.Root>,
        );

        expect(screen.getByTestId('trigger')).toBe(screen.getByRole('button'));
        expect(screen.getByRole('button')).toHaveAttribute('aria-haspopup', 'dialog');
      });

      it('handles interactions', async () => {
        const onOpenChange = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Popover.Root onOpenChange={onOpenChange}>
              <Toolbar.Button render={<Popover.Trigger />} />
              <Popover.Portal>
                <Popover.Positioner>
                  <Popover.Popup>Content</Popover.Popup>
                </Popover.Positioner>
              </Popover.Portal>
            </Popover.Root>
          </Toolbar.Root>,
        );

        expect(screen.queryByText('Content')).toBe(null);

        const trigger = screen.getByRole('button');
        await user.keyboard('[Tab]');
        expect(trigger).toHaveFocus();
        expect(onOpenChange).toHaveBeenCalledTimes(0);

        await user.keyboard('[Enter]');
        expect(screen.queryByText('Content')).not.toBe(null);
        expect(onOpenChange).toHaveBeenCalledTimes(1);
        expect(onOpenChange).toHaveBeenNthCalledWith(1, true, expect.anything());

        await user.keyboard('[Escape]');
        expect(onOpenChange).toHaveBeenCalledTimes(2);
        expect(onOpenChange).toHaveBeenNthCalledWith(2, false, expect.anything());
        await waitFor(() => {
          expect(trigger).toHaveFocus();
        });
      });

      it('disabled state', async () => {
        const onOpenChange = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Popover.Root onOpenChange={onOpenChange}>
              <Toolbar.Button disabled render={<Popover.Trigger />} />
              <Popover.Portal>
                <Popover.Positioner>
                  <Popover.Popup>Content</Popover.Popup>
                </Popover.Positioner>
              </Popover.Portal>
            </Popover.Root>
          </Toolbar.Root>,
        );

        expect(screen.queryByText('Content')).toBe(null);

        const trigger = screen.getByRole('button');
        expect(trigger).not.toHaveAttribute('disabled');
        expect(trigger).toHaveAttribute('data-disabled');
        expect(trigger).toHaveAttribute('aria-disabled', 'true');

        await user.keyboard('[Tab]');
        expect(trigger).toHaveFocus();
        expect(onOpenChange).toHaveBeenCalledTimes(0);

        await user.keyboard('[Enter]');
        await user.keyboard('[Space]');
        await user.keyboard('[ArrowUp]');
        await user.keyboard('[ArrowDown]');
        expect(onOpenChange).toHaveBeenCalledTimes(0);
      });
    });

    describe('Toggle and ToggleGroup', () => {
      it('renders toggle and toggle group', async () => {
        await render(
          <Toolbar.Root>
            <Toolbar.Button render={<Toggle />} value="apple" />
            <ToggleGroup>
              <Toolbar.Button render={<Toggle />} value="one" />
              <Toolbar.Button render={<Toggle />} value="two" />
            </ToggleGroup>
          </Toolbar.Root>,
        );

        expect(screen.getAllByRole('button').length).toBe(3);
        screen.getAllByRole('button').forEach((button) => {
          expect(button).toHaveAttribute('aria-pressed');
        });
      });

      it('handles interactions', async () => {
        const onPressedChange = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Toolbar.Button render={<Toggle onPressedChange={onPressedChange} />} value="apple" />
            <ToggleGroup>
              <Toolbar.Button render={<Toggle onPressedChange={onPressedChange} />} value="one" />
              <Toolbar.Button render={<Toggle onPressedChange={onPressedChange} />} value="two" />
            </ToggleGroup>
          </Toolbar.Root>,
        );

        const [button1, button2, button3] = screen.getAllByRole('button');

        [button1, button2, button3].forEach((button) => {
          expect(button).toHaveAttribute('aria-pressed', 'false');
        });
        expect(onPressedChange).toHaveBeenCalledTimes(0);

        await user.keyboard('[Tab]');
        await waitFor(() => {
          expect(button1).toHaveFocus();
        });

        await user.keyboard('[Enter]');
        expect(onPressedChange).toHaveBeenCalledTimes(1);
        expect(button1).toHaveAttribute('aria-pressed', 'true');

        await user.keyboard('[ArrowRight]');
        await waitFor(() => {
          expect(button2).toHaveFocus();
        });

        await user.keyboard('[Space]');
        expect(onPressedChange).toHaveBeenCalledTimes(2);
        expect(button2).toHaveAttribute('aria-pressed', 'true');

        await user.keyboard('[ArrowRight]');
        await waitFor(() => {
          expect(button3).toHaveFocus();
        });

        await user.keyboard('[Enter]');
        expect(onPressedChange).toHaveBeenCalledTimes(3);
        expect(button3).toHaveAttribute('aria-pressed', 'true');
      });

      it('disabled state', async () => {
        const onPressedChange = vi.fn();
        const { user } = await render(
          <Toolbar.Root>
            <Toolbar.Button
              disabled
              render={<Toggle onPressedChange={onPressedChange} />}
              value="apple"
            />
            <ToggleGroup>
              <Toolbar.Button
                disabled
                render={<Toggle onPressedChange={onPressedChange} />}
                value="one"
              />
              <Toolbar.Button
                disabled
                render={<Toggle onPressedChange={onPressedChange} />}
                value="two"
              />
            </ToggleGroup>
          </Toolbar.Root>,
        );
        const [button1, button2, button3] = screen.getAllByRole('button');

        [button1, button2, button3].forEach((button) => {
          expect(button).toHaveAttribute('aria-pressed', 'false');
          expect(button).not.toHaveAttribute('disabled');
          expect(button).toHaveAttribute('data-disabled');
          expect(button).toHaveAttribute('aria-disabled', 'true');
        });
        expect(onPressedChange).toHaveBeenCalledTimes(0);

        await user.keyboard('[Tab]');
        await waitFor(() => {
          expect(button1).toHaveFocus();
        });
        await user.keyboard('[Enter]');
        await user.keyboard('[Space]');
        expect(onPressedChange).toHaveBeenCalledTimes(0);

        await user.keyboard('[ArrowRight]');
        await waitFor(() => {
          expect(button2).toHaveFocus();
        });
        await user.keyboard('[Enter]');
        await user.keyboard('[Space]');
        expect(onPressedChange).toHaveBeenCalledTimes(0);

        await user.keyboard('[ArrowRight]');
        await waitFor(() => {
          expect(button3).toHaveFocus();
        });
        await user.keyboard('[Enter]');
        await user.keyboard('[Space]');
        expect(onPressedChange).toHaveBeenCalledTimes(0);
      });
    });
  });
});

// ---- packages/react/src/toolbar/group/ToolbarGroup.test.tsx ----
import { expect } from 'vitest';
import { Toolbar } from '@base-ui/react/toolbar';
import { screen } from '@mui/internal-test-utils';
import { createRenderer, describeConformance } from '#test-utils';
import { NOOP } from '../../internals/noop';
import { ToolbarRootContext } from '../root/ToolbarRootContext';
import { CompositeRootContext } from '../../internals/composite/root/CompositeRootContext';

const testCompositeContext: CompositeRootContext = {
  highlightedIndex: 0,
  onHighlightedIndexChange: NOOP,
  highlightItemOnHover: false,
  relayKeyboardEvent: NOOP,
};

const testToolbarContext: ToolbarRootContext = {
  disabled: false,
  orientation: 'horizontal',
  setItemMap: NOOP,
};

describe('<Toolbar.Group />', () => {
  const { render } = createRenderer();

  describeConformance(<Toolbar.Group />, () => ({
    refInstanceof: window.HTMLDivElement,
    render: (node) => {
      return render(
        <ToolbarRootContext.Provider value={testToolbarContext}>
          <CompositeRootContext.Provider value={testCompositeContext}>
            {node}
          </CompositeRootContext.Provider>
        </ToolbarRootContext.Provider>,
      );
    },
  }));

  describe('ARIA attributes', () => {
    it('renders a group', async () => {
      await render(
        <Toolbar.Root>
          <Toolbar.Group data-testid="group" />
        </Toolbar.Root>,
      );

      expect(screen.getByTestId('group')).toBe(screen.getByRole('group'));
    });
  });

  describe('prop: disabled', () => {
    it('disables all toolbar items except links in the group', async () => {
      await render(
        <Toolbar.Root>
          <Toolbar.Group disabled>
            <Toolbar.Button />
            <Toolbar.Link href="https://base-ui.com">Link</Toolbar.Link>
            <Toolbar.Input defaultValue="" />
          </Toolbar.Group>
        </Toolbar.Root>,
      );

      [screen.getByRole('button'), screen.getByRole('textbox')].forEach((toolbarItem) => {
        expect(toolbarItem).toHaveAttribute('aria-disabled', 'true');
        expect(toolbarItem).toHaveAttribute('data-disabled');
      });

      expect(screen.getByText('Link')).not.toHaveAttribute('data-disabled');
      expect(screen.getByText('Link')).not.toHaveAttribute('aria-disabled');
    });
  });
});

// ---- packages/react/src/toolbar/input/ToolbarInput.test.tsx ----
import { expect, vi } from 'vitest';
import { Toolbar } from '@base-ui/react/toolbar';
import { NumberField } from '@base-ui/react/number-field';
import { screen } from '@mui/internal-test-utils';
import { createRenderer, describeConformance, isJSDOM } from '#test-utils';
import { NOOP } from '../../internals/noop';
import { ToolbarRootContext } from '../root/ToolbarRootContext';
import { type Orientation } from '../../internals/types';
import { CompositeRootContext } from '../../internals/composite/root/CompositeRootContext';
import { ARROW_UP, ARROW_DOWN, ARROW_LEFT, ARROW_RIGHT } from '../../internals/composite/composite';

const testCompositeContext: CompositeRootContext = {
  highlightedIndex: 0,
  onHighlightedIndexChange: NOOP,
  highlightItemOnHover: false,
  relayKeyboardEvent: NOOP,
};

const testToolbarContext: ToolbarRootContext = {
  disabled: false,
  orientation: 'horizontal',
  setItemMap: NOOP,
};

describe('<Toolbar.Input />', () => {
  const { render } = createRenderer();

  describeConformance(<Toolbar.Input />, () => ({
    refInstanceof: window.HTMLInputElement,
    testRenderPropWith: 'input',
    render: (node) => {
      return render(
        <ToolbarRootContext.Provider value={testToolbarContext}>
          <CompositeRootContext.Provider value={testCompositeContext}>
            {node}
          </CompositeRootContext.Provider>
        </ToolbarRootContext.Provider>,
      );
    },
  }));

  describe('ARIA attributes', () => {
    it('renders a textbox', async () => {
      await render(
        <Toolbar.Root>
          <Toolbar.Input data-testid="input" />
        </Toolbar.Root>,
      );

      expect(screen.getByTestId('input')).toBe(screen.getByRole('textbox'));
    });
  });

  describe.skipIf(isJSDOM)('keyboard navigation', () => {
    // when navigating through RTL text in real browsers the arrow keys for
    // moving the text insertion cursor is also reversed from LTR but this doesn't
    // work with testing library
    [
      ['horizontal', ARROW_RIGHT, ARROW_LEFT],
      ['vertical', ARROW_DOWN, ARROW_UP],
    ].forEach((entry) => {
      const [orientation, nextKey, prevKey] = entry;

      it(`orientation: ${orientation}`, async () => {
        const { user } = await render(
          <Toolbar.Root orientation={orientation as Orientation}>
            <Toolbar.Button />
            <Toolbar.Input defaultValue="abcd" />
            <Toolbar.Button />
          </Toolbar.Root>,
        );
        const input = screen.getByRole('textbox') as HTMLInputElement;
        const [button1, button2] = screen.getAllByRole('button');

        await user.keyboard('[Tab]');
        expect(button1).toHaveFocus();

        await user.keyboard(`[${nextKey}]`);
        expect(input).toHaveFocus();

        // Firefox doesn't support document.getSelection() in inputs
        expect(input.selectionStart).toBe(0);
        expect(input.selectionEnd).toBe(4);

        await user.keyboard(`[${ARROW_RIGHT}]`);
        await user.keyboard(`[${nextKey}]`);

        expect(button2).toHaveFocus();

        await user.keyboard(`[${prevKey}]`);
        expect(input).toHaveFocus();

        await user.keyboard(`[${ARROW_LEFT}]`);
        await user.keyboard(`[${prevKey}]`);

        expect(button1).toHaveFocus();
      });
    });
  });

  describe('rendering NumberField', () => {
    it('renders NumberField.Input', async () => {
      await render(
        <Toolbar.Root>
          <NumberField.Root>
            <NumberField.Group>
              <Toolbar.Input render={<NumberField.Input />} />
            </NumberField.Group>
          </NumberField.Root>
        </Toolbar.Root>,
      );

      expect(screen.getByRole('textbox')).toHaveAttribute('aria-roledescription', 'Number field');
    });

    it('handles interactions', async () => {
      const onValueChange = vi.fn();
      const { user } = await render(
        <Toolbar.Root>
          <NumberField.Root min={1} max={10} defaultValue={5} onValueChange={onValueChange}>
            <NumberField.Group>
              <NumberField.Decrement />
              <Toolbar.Input render={<NumberField.Input />} />
              <NumberField.Increment />
            </NumberField.Group>
          </NumberField.Root>
        </Toolbar.Root>,
      );

      const input = screen.getByRole('textbox');

      await user.keyboard('[Tab]');
      expect(input).toHaveAttribute('tabindex', '0');
      expect(input).toHaveFocus();

      await user.keyboard(`[${ARROW_UP}]`);
      expect(onValueChange.mock.calls.length).toBe(1);
      expect(onValueChange.mock.calls[0][0]).toBe(6);

      await user.keyboard(`[${ARROW_DOWN}]`);
      expect(onValueChange.mock.calls.length).toBe(2);
      expect(onValueChange.mock.calls[1][0]).toBe(5);
    });

    it('disabled state', async () => {
      const onValueChange = vi.fn();
      const { user } = await render(
        <Toolbar.Root>
          <NumberField.Root min={1} max={10} defaultValue={5} onValueChange={onValueChange}>
            <NumberField.Group>
              <NumberField.Decrement />
              <Toolbar.Input disabled render={<NumberField.Input />} />
              <NumberField.Increment />
            </NumberField.Group>
          </NumberField.Root>
        </Toolbar.Root>,
      );

      const input = screen.getByRole('textbox');

      expect(input).not.toHaveAttribute('disabled');
      expect(input).toHaveAttribute('data-disabled');
      expect(input).toHaveAttribute('aria-disabled', 'true');

      await user.keyboard('[Tab]');
      expect(input).toHaveAttribute('tabindex', '0');
      expect(input).toHaveFocus();

      await user.keyboard(`[${ARROW_UP}]`);
      await user.keyboard(`[${ARROW_DOWN}]`);
      expect(onValueChange.mock.calls.length).toBe(0);
    });
  });
});

// ---- packages/react/src/toolbar/link/ToolbarLink.test.tsx ----
import { expect } from 'vitest';
import { Toolbar } from '@base-ui/react/toolbar';
import { screen } from '@mui/internal-test-utils';
import { createRenderer, describeConformance } from '#test-utils';
import { NOOP } from '../../internals/noop';
import { ToolbarRootContext } from '../root/ToolbarRootContext';
import { CompositeRootContext } from '../../internals/composite/root/CompositeRootContext';

const testCompositeContext: CompositeRootContext = {
  highlightedIndex: 0,
  onHighlightedIndexChange: NOOP,
  highlightItemOnHover: false,
  relayKeyboardEvent: NOOP,
};

const testToolbarContext: ToolbarRootContext = {
  disabled: false,
  orientation: 'horizontal',
  setItemMap: NOOP,
};

describe('<Toolbar.Link />', () => {
  const { render } = createRenderer();

  describeConformance(<Toolbar.Link />, () => ({
    refInstanceof: window.HTMLAnchorElement,
    testRenderPropWith: 'a',
    render: (node) => {
      return render(
        <ToolbarRootContext.Provider value={testToolbarContext}>
          <CompositeRootContext.Provider value={testCompositeContext}>
            {node}
          </CompositeRootContext.Provider>
        </ToolbarRootContext.Provider>,
      );
    },
  }));

  describe('ARIA attributes', () => {
    it('renders an anchor', async () => {
      await render(
        <Toolbar.Root>
          <Toolbar.Link data-testid="link" href="https://base-ui.com" />
        </Toolbar.Root>,
      );

      expect(screen.getByTestId('link')).toBe(screen.getByRole('link'));
    });
  });
});

// ---- packages/react/src/toolbar/root/ToolbarRoot.test.tsx ----
import { expect } from 'vitest';
import { Toolbar } from '@base-ui/react/toolbar';
import { DirectionProvider, type TextDirection } from '@base-ui/react/direction-provider';
import { screen } from '@mui/internal-test-utils';
import { createRenderer, describeConformance, isJSDOM } from '#test-utils';
import { type Orientation } from '../../internals/types';

describe('<Toolbar.Root />', () => {
  const { render } = createRenderer();

  describeConformance(<Toolbar.Root />, () => ({
    refInstanceof: window.HTMLDivElement,
    render,
  }));

  describe('ARIA attributes', () => {
    it('has role="toolbar"', async () => {
      const { container } = await render(<Toolbar.Root />);

      expect(container.firstElementChild as HTMLElement).toHaveAttribute('role', 'toolbar');
    });
  });

  describe.skipIf(isJSDOM)('keyboard navigation', () => {
    [
      ['ltr', 'horizontal', 'ArrowRight', 'ArrowLeft'],
      ['ltr', 'vertical', 'ArrowDown', 'ArrowUp'],
      ['rtl', 'horizontal', 'ArrowLeft', 'ArrowRight'],
      ['rtl', 'vertical', 'ArrowDown', 'ArrowUp'],
    ].forEach((entry) => {
      const [direction, orientation, nextKey, prevKey] = entry;

      describe(direction, () => {
        it(`orientation: ${orientation}`, async () => {
          const { user } = await render(
            <DirectionProvider direction={direction as TextDirection}>
              <Toolbar.Root dir={direction} orientation={orientation as Orientation}>
                <Toolbar.Button />
                <Toolbar.Link href="https://base-ui.com">Link</Toolbar.Link>
                <Toolbar.Group>
                  <Toolbar.Button />
                  <Toolbar.Button />
                </Toolbar.Group>
                <Toolbar.Input defaultValue="" />
              </Toolbar.Root>
            </DirectionProvider>,
          );
          const [button1, groupedButton1, groupedButton2] = screen.getAllByRole('button');
          const link = screen.getByText('Link');
          const input = screen.getByRole('textbox');

          await user.keyboard('[Tab]');
          expect(button1).toHaveFocus();

          await user.keyboard(`[${nextKey}]`);
          expect(link).toHaveFocus();

          await user.keyboard(`[${nextKey}]`);
          expect(groupedButton1).toHaveFocus();

          await user.keyboard(`[${nextKey}]`);
          expect(groupedButton2).toHaveFocus();

          await user.keyboard(`[${nextKey}]`);
          expect(input).toHaveFocus();

          // loop to the beginning
          await user.keyboard(`[${nextKey}]`);
          expect(button1).toHaveFocus();

          await user.keyboard(`[${prevKey}]`);
          expect(input).toHaveFocus();

          await user.keyboard(`[${prevKey}]`);
          expect(groupedButton2).toHaveFocus();
        });
      });
    });
  });

  describe('prop: disabled', () => {
    it('disables all toolbar items except links', async () => {
      await render(
        <Toolbar.Root disabled>
          <Toolbar.Button />
          <Toolbar.Link href="https://base-ui.com">Link</Toolbar.Link>
          <Toolbar.Input defaultValue="" />
          <Toolbar.Group>
            <Toolbar.Button />
            <Toolbar.Link href="https://base-ui.com">Link</Toolbar.Link>
            <Toolbar.Input defaultValue="" />
          </Toolbar.Group>
        </Toolbar.Root>,
      );

      [...screen.getAllByRole('button'), ...screen.getAllByRole('textbox')].forEach(
        (toolbarItem) => {
          expect(toolbarItem).toHaveAttribute('aria-disabled', 'true');
          expect(toolbarItem).toHaveAttribute('data-disabled');
        },
      );

      expect(screen.getByRole('group')).toHaveAttribute('data-disabled');

      screen.getAllByText('Link').forEach((link) => {
        expect(link).not.toHaveAttribute('data-disabled');
        expect(link).not.toHaveAttribute('aria-disabled');
      });
    });
  });

  describe.skipIf(isJSDOM)('prop: focusableWhenDisabled', () => {
    function expectFocusedWhenDisabled(element: Element) {
      expect(element).toHaveAttribute('data-disabled');
      expect(element).toHaveAttribute('aria-disabled', 'true');
      expect(element).toHaveFocus();
    }

    it('toolbar items can be focused when disabled by default', async () => {
      const { user } = await render(
        <Toolbar.Root>
          <Toolbar.Button disabled />
          <Toolbar.Group>
            <Toolbar.Button disabled />
            <Toolbar.Button disabled />
          </Toolbar.Group>
          <Toolbar.Input defaultValue="" disabled />
        </Toolbar.Root>,
      );

      const input = screen.getByRole('textbox');
      const buttons = screen.getAllByRole('button');
      [input, ...buttons].forEach((item) => {
        expect(item).not.toHaveAttribute('disabled');
      });

      const [button1, groupedButton1, groupedButton2] = buttons;

      await user.keyboard('[Tab]');
      expect(button1).toHaveFocus();

      await user.keyboard('[ArrowRight]');
      expectFocusedWhenDisabled(groupedButton1);

      await user.keyboard('[ArrowRight]');
      expectFocusedWhenDisabled(groupedButton2);

      await user.keyboard('[ArrowRight]');
      expectFocusedWhenDisabled(input);

      // loop to the beginning
      await user.keyboard('[ArrowRight]');
      expect(button1).toHaveAttribute('tabindex', '0');

      await user.keyboard('[ArrowLeft]');
      expectFocusedWhenDisabled(input);

      await user.keyboard('[ArrowLeft]');
      expectFocusedWhenDisabled(groupedButton2);
    });

    it('toolbar items can individually disable focusableWhenDisabled', async () => {
      const { user } = await render(
        <Toolbar.Root>
          <Toolbar.Button disabled />
          <Toolbar.Group>
            <Toolbar.Button disabled />
            <Toolbar.Button disabled focusableWhenDisabled={false} />
          </Toolbar.Group>
          <Toolbar.Input defaultValue="" disabled />
        </Toolbar.Root>,
      );

      const input = screen.getByRole('textbox');
      const buttons = screen.getAllByRole('button');
      const focusableWhenDisabledButtons = buttons.filter(
        (button) => button.getAttribute('data-focusable') != null,
      );
      [input, ...focusableWhenDisabledButtons].forEach((item) => {
        expect(item).not.toHaveAttribute('disabled');
      });

      const [button1, groupedButton1, groupedButton2] = buttons;
      expect(groupedButton2).toHaveAttribute('disabled');

      await user.keyboard('[Tab]');
      expect(button1).toHaveFocus();

      await user.keyboard('[ArrowRight]');
      expectFocusedWhenDisabled(groupedButton1);

      await user.keyboard('[ArrowRight]');
      expectFocusedWhenDisabled(input);

      // loop to the beginning
      await user.keyboard('[ArrowRight]');
      expect(button1).toHaveAttribute('tabindex', '0');

      await user.keyboard('[ArrowLeft]');
      expectFocusedWhenDisabled(input);

      await user.keyboard('[ArrowLeft]');
      expectFocusedWhenDisabled(groupedButton1);
    });
  });
});

