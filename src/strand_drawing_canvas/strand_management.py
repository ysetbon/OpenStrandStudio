import logging
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from strand import Strand, AttachedStrand, MaskedStrand

class StrandManagementMixin:
    def on_strand_created(self, strand):
        logging.info(f"Starting on_strand_created for strand: {strand.layer_name}")
        
        if hasattr(strand, 'is_being_deleted') and strand.is_being_deleted:
            logging.info("Strand is being deleted, skipping creation process")
            return

        if isinstance(strand, AttachedStrand):
            set_number = strand.parent.set_number
        elif self.selected_strand:
            set_number = self.selected_strand.set_number
        else:
            set_number = max(self.strand_colors.keys(), default=0) + 1

        strand.set_number = set_number

        if set_number not in self.strand_colors:
            self.strand_colors[set_number] = QColor('purple')
        strand.set_color(self.strand_colors[set_number])

        self.strands.append(strand)
        self.newest_strand = strand

        if self.layer_panel:
            set_number = int(strand.set_number) if isinstance(strand.set_number, str) else strand.set_number
            count = len([s for s in self.strands if s.set_number == set_number])
            strand.layer_name = f"{set_number}_{count}"
            
            if not hasattr(strand, 'is_being_deleted'):
                logging.info(f"Adding new layer button for set {set_number}, count {count}")
                self.layer_panel.add_layer_button(set_number, count)
            else:
                logging.info(f"Updating layer names for set {set_number}")
                self.layer_panel.update_layer_names(set_number)
            
            self.layer_panel.on_color_changed(set_number, self.strand_colors[set_number])

        if not isinstance(strand, AttachedStrand):
            self.select_strand(len(self.strands) - 1)
        
        self.update()
        
        if self.layer_panel:
            self.layer_panel.update_attachable_states()
        
        logging.info("Finished on_strand_created")

    def attach_strand(self, parent_strand, new_strand):
        parent_strand.attached_strands.append(new_strand)
        new_strand.parent = parent_strand
        new_strand.set_number = parent_strand.set_number
        self.strands.append(new_strand)
        self.newest_strand = new_strand
        count = len([s for s in self.strands if s.set_number == new_strand.set_number])
        new_strand.layer_name = f"{new_strand.set_number}_{count}"
        
        if new_strand.set_number in self.strand_colors:
            new_strand.set_color(self.strand_colors[new_strand.set_number])
        
        if self.layer_panel:
            if not hasattr(new_strand, 'is_being_deleted'):
                self.layer_panel.add_layer_button(new_strand.set_number, count)
            else:
                self.layer_panel.update_layer_names(new_strand.set_number)
            self.layer_panel.on_strand_attached()
        
        self.update()
        logging.info(f"Attached new strand: {new_strand.layer_name} to parent: {parent_strand.layer_name}")

    def move_strand_to_top(self, strand):
        if strand in self.strands:
            self.strands.remove(strand)
            self.strands.append(strand)
            
            if self.layer_panel:
                current_index = self.layer_panel.layer_buttons.index(
                    next(button for button in self.layer_panel.layer_buttons if button.text() == strand.layer_name)
                )
                button = self.layer_panel.layer_buttons.pop(current_index)
                self.layer_panel.layer_buttons.insert(0, button)
                self.layer_panel.refresh()
            
            self.update()
            logging.info(f"Moved strand {strand.layer_name} to top")
        else:
            logging.warning(f"Attempted to move non-existent strand to top: {strand.layer_name}")

    def add_strand(self, strand):
        self.strands.append(strand)
        self.update()

    def remove_strand(self, strand):
        logging.info(f"Starting remove_strand for: {strand.layer_name}")

        if strand not in self.strands:
            logging.warning(f"Strand {strand.layer_name} not found in self.strands")
            return

        set_number, strand_number = map(int, strand.layer_name.split('_')[:2])
        
        if strand == self.newest_strand:
            self.newest_strand = None
        
        is_main_strand = strand_number == 1

        if not is_main_strand:
            self.strands.remove(strand)
            logging.info(f"Removed attached strand: {strand.layer_name}")

            parent_strand = self.find_parent_strand(strand)
            if parent_strand:
                parent_strand.attached_strands.remove(strand)
                logging.info(f"Updated parent strand: {parent_strand.layer_name}, remaining attached strands: {[s.layer_name for s in parent_strand.attached_strands]}")

                self.remove_parent_circle(parent_strand, strand)

            self.remove_related_masked_layers(strand)
        else:
            strands_to_remove = [strand] + self.get_all_attached_strands(strand) + self.get_all_related_masked_strands(strand)
            logging.info(f"Main strand identified. Preparing to remove main strand and related strands: {[s.layer_name for s in strands_to_remove]}")

            for s in strands_to_remove:
                if s in self.strands:
                    self.strands.remove(s)
                    logging.info(f"Removed strand: {s.layer_name}")
                    self.remove_strand_circles(s)

            self.remove_related_masked_layers(strand)
            self.update_layer_names_for_set(set_number)
            self.update_set_numbers_after_main_strand_deletion(set_number)

        if self.selected_strand == strand:
            self.selected_strand = None
            self.selected_strand_index = None
            logging.info("Cleared selected strand")

        if self.layer_panel:
            logging.info("Refreshing layer panel")
            self.layer_panel.refresh()

        self.update()
        QTimer.singleShot(0, self.update)
        logging.info("Finished remove_strand")

    def remove_related_masked_layers(self, strand):
        masked_layers_before = len(self.strands)
        self.strands = [s for s in self.strands if not (isinstance(s, MaskedStrand) and self.is_strand_involved_in_mask(s, strand))]
        masked_layers_removed = masked_layers_before - len(self.strands)
        logging.info(f"Removed related masked layers. Total masked layers removed: {masked_layers_removed}")

    def remove_strand_circles(self, strand):
        if hasattr(strand, 'has_circles'):
            if strand.has_circles[0]:
                strand.has_circles[0] = False
                logging.info(f"Removed start circle for strand: {strand.layer_name}")
            if strand.has_circles[1]:
                strand.has_circles[1] = False
                logging.info(f"Removed end circle for strand: {strand.layer_name}")

    def get_all_related_masked_strands(self, strand):
        return [s for s in self.strands if isinstance(s, MaskedStrand) and self.is_strand_involved_in_mask(s, strand)]

    def remove_parent_circle(self, parent_strand, attached_strand):
        if parent_strand.end == attached_strand.start:
            other_attachments = [s for s in parent_strand.attached_strands if s != attached_strand and s.start == parent_strand.end]
            if not other_attachments:
                parent_strand.has_circles[1] = False
                logging.info(f"Removed circle from the end of parent strand: {parent_strand.layer_name}")
        elif parent_strand.start == attached_strand.start:
            other_attachments = [s for s in parent_strand.attached_strands if s != attached_strand and s.start == parent_strand.start]
            if not other_attachments:
                parent_strand.has_circles[0] = False
                logging.info(f"Removed circle from the start of parent strand: {parent_strand.layer_name}")

    def is_strand_involved_in_mask(self, masked_strand, strand):
        masked_parts = masked_strand.layer_name.split('_')
        return any(part == strand.layer_name for part in masked_parts) or strand.layer_name in masked_strand.layer_name

    def get_all_attached_strands(self, strand):
        attached = []
        for attached_strand in strand.attached_strands:
            attached.append(attached_strand)
            attached.extend(self.get_all_attached_strands(attached_strand))
        return attached

    def find_parent_strand(self, attached_strand):
        for strand in self.strands:
            if attached_strand in strand.attached_strands:
                return strand
        return None

    def create_masked_strand(self, strand1, strand2):
        masked_strand = MaskedStrand(strand1, strand2)
        self.strands.append(masked_strand)
        self.update()
        return masked_strand

    def unmerge_masked_strand(self, masked_strand):
        if masked_strand in self.strands:
            self.strands.remove(masked_strand)
            self.update()

    def update_strand_position(self, strand, new_start, new_end):
        strand.start = new_start
        strand.end = new_end
        strand.update_shape()
        self.update()

    def get_strand_by_name(self, layer_name):
        for strand in self.strands:
            if strand.layer_name == layer_name:
                return strand
        return None

    def get_strands_in_rect(self, rect):
        return [strand for strand in self.strands if strand.get_path().intersects(rect)]

    def clear_all_strands(self):
        self.strands.clear()
        self.selected_strand = None
        self.selected_strand_index = None
        self.newest_strand = None
        self.update()
        if self.layer_panel:
            self.layer_panel.refresh()

    def duplicate_strand(self, strand):
        new_strand = strand.duplicate()
        self.strands.append(new_strand)
        self.on_strand_created(new_strand)
        return new_strand

    def get_strand_count(self):
        return len(self.strands)

    def get_main_strands(self):
        return [strand for strand in self.strands if isinstance(strand, Strand) and not isinstance(strand, AttachedStrand)]

    def get_attached_strands(self):
        return [strand for strand in self.strands if isinstance(strand, AttachedStrand)]

    def get_masked_strands(self):
        return [strand for strand in self.strands if isinstance(strand, MaskedStrand)]

    def update_strand_colors(self):
        for strand in self.strands:
            if strand.set_number in self.strand_colors:
                strand.set_color(self.strand_colors[strand.set_number])
        self.update()